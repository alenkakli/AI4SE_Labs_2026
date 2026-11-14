from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import re
import textwrap
from pathlib import Path
from typing import Any, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[3]
ASSIGNMENTS_ROOT = REPO_ROOT / "Week_06_Implementation" / "Assignments"
MISSING_CODE_PATH = ASSIGNMENTS_ROOT / "missing_code.json"
PROJECT_ROOT = ASSIGNMENTS_ROOT / "Task_1" / "AI4SE_Playground"
PLAYGROUND_ROOT = PROJECT_ROOT
EMBEDDINGS_PATH = ASSIGNMENTS_ROOT / "Task_3" / "chunk_embeddings.json"
ALLOWED_MODELS = [
    "gpt-6-luna",
    "gpt-5.6-luna",
    "gpt-5.4-nano",
    "gpt-5-nano",
    "gpt-5-mini",
    "gpt-4.1-nano",
    "gpt-4o-mini",
]


def _load_match_embeddings_module() -> Any:
    match_module_path = ASSIGNMENTS_ROOT / "Task_4" / "match_embeddings.py"
    spec = importlib.util.spec_from_file_location("match_embeddings", match_module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {match_module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MATCH_EMBEDDINGS = _load_match_embeddings_module()


def load_missing_tasks(path: Path = MISSING_CODE_PATH) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError(f"Expected a list of tasks in {path}")
    return payload


def normalize_task_text(task: dict[str, Any]) -> str:
    parts = [
        str(task.get("file", "")),
        str(task.get("class", "")),
        str(task.get("method", "")),
        str(task.get("docstring", "")),
    ]
    return " ".join(part.strip() for part in parts if part and part.strip())


def retrieve_top_matches(task: str, top_k: int = 5) -> list[dict[str, Any]]:
    return MATCH_EMBEDDINGS.retrieve_for_query(task, storage_path=EMBEDDINGS_PATH, top_k=top_k)


def build_prompt(task: dict[str, Any], matches: Sequence[dict[str, Any]]) -> str:
    task_text = task.get("docstring", "")
    target = f"{task.get('file')}::{task.get('class')}.{task.get('method')}"

    snippets = []
    for match in matches:
        snippet = (
            f"- file: {match.get('file')}\n"
            f"  symbol: {match.get('symbol') or 'unknown'}\n"
            f"  range: {match.get('start_line')}:{match.get('end_line')}\n"
            f"  preview: {match.get('preview', '').strip()}\n"
        )
        snippets.append(snippet)

    return textwrap.dedent(
        f"""
        Fix the Python implementation for the target method below.

        Target: {target}
        Task summary: {task_text}

        Use the repository context below to infer the correct implementation.
        Return only the method implementation as valid Python source; do not include markdown fences or commentary.

        Relevant chunks:
        {''.join(snippets) if snippets else 'None'}
        """
    ).strip()


def extract_code(response: str) -> str:
    response = response.strip()
    match = re.search(r"```(?:python)?\s*(.*?)```", response, flags=re.DOTALL | re.IGNORECASE)
    if match:
        response = match.group(1).strip()
    return response.strip()


def _method_signature(source: str, class_name: str, method_name: str) -> tuple[int, int, str]:
    module = ast.parse(source)
    for node in ast.walk(module):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == method_name:
                    start_line = child.lineno
                    end_line = child.end_lineno or child.lineno
                    prefix = source.splitlines()[start_line - 1]
                    header_match = re.search(rf"def\s+{re.escape(method_name)}\s*\(.*?\):", prefix)
                    if header_match is None:
                        # Fall back to the already-declared signature in the file.
                        header = f"def {method_name}(self):"
                    else:
                        header = header_match.group(0)
                    return start_line, end_line, header
    raise ValueError(f"Could not locate {class_name}.{method_name} in the source file")


def replace_method(file_path: Path, class_name: str, method_name: str, new_impl: str) -> None:
    source = file_path.read_text(encoding="utf-8")
    module = ast.parse(source)
    method_node = None
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == method_name:
                    method_node = child
                    break
    if method_node is None:
        raise ValueError(f"No method {class_name}.{method_name} in {file_path}")

    lines = source.splitlines()
    start = method_node.lineno - 1
    end = method_node.end_lineno
    signature = "".join(lines[start : start + 1])
    header_match = re.search(rf"def\s+{re.escape(method_name)}\s*\(.*?\):", signature)
    indent = " " * method_node.col_offset
    if header_match is None:
        header = f"{indent}def {method_name}(self):"
    else:
        header = f"{indent}{header_match.group(0)}"

    body = new_impl.strip()
    if not body:
        raise ValueError(f"Empty implementation returned for {class_name}.{method_name}")
    block = textwrap.indent(body, " " * (method_node.col_offset + 4))
    replacement = header + "\n" + block + "\n"
    new_lines = lines[:start] + replacement.splitlines() + lines[end:]
    file_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def call_llm(prompt: str, model: str) -> str:
    model = model.strip()
    if model not in ALLOWED_MODELS:
        raise ValueError(f"Unsupported model: {model}. Allowed: {', '.join(ALLOWED_MODELS)}")

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No API key is configured. Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY to use the LLM-backed solver."
        )

    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError("The openai package is not installed.") from exc

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content


def solve_task(task: dict[str, Any], model: str, top_k: int = 5) -> dict[str, Any]:
    matches = retrieve_top_matches(normalize_task_text(task), top_k=top_k)
    prompt = build_prompt(task, matches)
    response = call_llm(prompt, model)
    code = extract_code(response)
    file_name = task["file"]
    target_path = PLAYGROUND_ROOT / file_name
    target_path = target_path.resolve()
    replace_method(target_path, task["class"], task["method"], code)
    return {"file": str(target_path), "class": task["class"], "method": task["method"], "matches": matches}


def run_all_tasks(model: str, top_k: int = 5) -> list[dict[str, Any]]:
    results = []
    for task in load_missing_tasks():
        results.append(solve_task(task, model=model, top_k=top_k))
    return results


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Use a chunk-retrieval + LLM pipeline to implement missing project methods.")
    parser.add_argument("--model", default=os.getenv("LLM_MODEL", "gpt-5-mini"), choices=ALLOWED_MODELS)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--task-file", type=Path, default=MISSING_CODE_PATH)
    parser.add_argument("--class-name", help="Optional class to target when solving a single task.")
    parser.add_argument("--method-name", help="Optional method to target when solving a single task.")
    parser.add_argument("--task-text", help="Optional plain-language task description for a single retrieval prompt.")
    parser.add_argument("--dry-run", action="store_true", help="Only print the planned prompt and matching chunks without writing files.")
    return parser


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    if args.task_text or args.class_name or args.method_name:
        if not args.task_text:
            raise SystemExit("--task-text is required when using a single-task mode.")
        if not args.class_name or not args.method_name:
            raise SystemExit("--class-name and --method-name are required together in single-task mode.")
        task = {
            "file": "playground/playground/__init__.py",
            "class": args.class_name,
            "method": args.method_name,
            "docstring": args.task_text,
        }
        if args.dry_run:
            matches = retrieve_top_matches(args.task_text, top_k=args.top_k)
            print(json.dumps(build_prompt(task, matches), indent=2, ensure_ascii=False))
            return
        solve_task(task, model=args.model, top_k=args.top_k)
        return

    tasks = load_missing_tasks(args.task_file)
    for task in tasks:
        if args.dry_run:
            matches = retrieve_top_matches(normalize_task_text(task), top_k=args.top_k)
            print(json.dumps({"task": task, "matches": matches[:args.top_k]}, indent=2, ensure_ascii=False))
            continue
        solve_task(task, model=args.model, top_k=args.top_k)


if __name__ == "__main__":
    main()
