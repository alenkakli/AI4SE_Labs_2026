from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_PATH = Path(__file__).resolve().with_name("repository_chunks.json")

EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "site-packages",
    ".mypy_cache",
    ".pytest_cache",
    ".ipynb_checkpoints",
}

TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".csv",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".env",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".css",
    ".sql",
    ".xml",
}

TARGET_CHARS = 3500
OVERLAP_CHARS = 500
MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")

Chunk = Dict[str, object]


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def iter_source_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if (
            not should_skip(path)
            and path.is_file()
            and path.resolve() != OUTPUT_PATH
            and path.suffix.lower() in TEXT_SUFFIXES
        ):
            yield path


def make_chunk(
    file_path: str,
    start_line: int,
    end_line: int,
    text: str,
    kind: str,
    symbol: Optional[str] = None,
) -> Chunk:
    chunk: Chunk = {
        "file": file_path,
        "kind": kind,
        "start_line": start_line,
        "end_line": end_line,
        "text": text,
    }
    if symbol:
        chunk["symbol"] = symbol
    return chunk


def split_lines(
    lines: List[str],
    file_path: str,
    start_line: int,
    kind: str,
    symbol: Optional[str] = None,
) -> List[Chunk]:
    chunks: List[Chunk] = []
    current: List[str] = []
    current_size = 0
    current_start = start_line

    def flush() -> None:
        nonlocal current, current_size, current_start
        text = "\n".join(current).strip()
        if text:
            chunks.append(
                make_chunk(
                    file_path,
                    current_start,
                    current_start + len(current) - 1,
                    text,
                    kind,
                    symbol,
                )
            )

    for line_number, line in enumerate(lines, start=start_line):
        if len(line) > TARGET_CHARS:
            if current:
                flush()
                current = []
                current_size = 0
            step = TARGET_CHARS - OVERLAP_CHARS
            for offset in range(0, len(line), step):
                piece = line[offset : offset + TARGET_CHARS]
                chunks.append(
                    make_chunk(file_path, line_number, line_number, piece, kind, symbol)
                )
            continue

        piece_size = len(line) + 1
        if current and current_size + piece_size > TARGET_CHARS:
            flush()
            overlap: List[str] = []
            overlap_size = 0
            for previous in reversed(current):
                overlap.append(previous)
                overlap_size += len(previous) + 1
                if overlap_size >= OVERLAP_CHARS:
                    break
            current = list(reversed(overlap))
            current_size = sum(len(part) + 1 for part in current)
            while current and current_size + piece_size > TARGET_CHARS:
                removed = current.pop(0)
                current_size -= len(removed) + 1
            current_start = line_number - len(current)

        if not current:
            current_start = line_number
        current.append(line)
        current_size += piece_size

    if current:
        flush()
    return chunks


def add_source_unit(
    chunks: List[Chunk],
    source_lines: List[str],
    file_path: str,
    start_line: int,
    end_line: int,
    kind: str,
    symbol: Optional[str] = None,
) -> None:
    text = "\n".join(source_lines[start_line - 1 : end_line]).strip()
    if not text:
        return
    if len(text) <= TARGET_CHARS:
        chunks.append(make_chunk(file_path, start_line, end_line, text, kind, symbol))
    else:
        chunks.extend(
            split_lines(
                source_lines[start_line - 1 : end_line],
                file_path,
                start_line,
                kind,
                symbol,
            )
        )


def node_start(node: ast.AST) -> int:
    decorator_lines = [
        decorator.lineno
        for decorator in getattr(node, "decorator_list", [])
        if hasattr(decorator, "lineno")
    ]
    return min(decorator_lines, default=node.lineno)


def node_name(node: ast.AST) -> Optional[str]:
    name = getattr(node, "name", None)
    if name:
        return str(name)
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        target = node.targets[0] if isinstance(node, ast.Assign) else node.target
        if isinstance(target, ast.Name):
            return target.id
    return None


def chunk_python(text: str, file_path: str) -> List[Chunk]:
    source_lines = text.splitlines()
    try:
        tree = ast.parse(text, filename=file_path)
    except SyntaxError:
        return split_lines(source_lines, file_path, 1, "fallback")

    chunks: List[Chunk] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            add_source_unit(
                chunks,
                source_lines,
                file_path,
                node_start(node),
                node.end_lineno or node.lineno,
                "function",
                node.name,
            )
        elif isinstance(node, ast.ClassDef):
            methods = [
                member
                for member in node.body
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            class_symbol = node.name
            class_body_start = node_start(node.body[0]) if node.body else (node.end_lineno or node.lineno)
            if methods:
                add_source_unit(
                    chunks,
                    source_lines,
                    file_path,
                    node_start(node),
                    class_body_start - 1,
                    "class",
                    class_symbol,
                )
                for member in node.body:
                    if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        add_source_unit(
                            chunks,
                            source_lines,
                            file_path,
                            node_start(member),
                            member.end_lineno or member.lineno,
                            "method",
                            f"{class_symbol}.{member.name}",
                        )
                    else:
                        member_name = node_name(member)
                        add_source_unit(
                            chunks,
                            source_lines,
                            file_path,
                            node_start(member),
                            member.end_lineno or member.lineno,
                            "class_member",
                            f"{class_symbol}.{member_name}" if member_name else class_symbol,
                        )
            else:
                add_source_unit(
                    chunks,
                    source_lines,
                    file_path,
                    node_start(node),
                    node.end_lineno or node.lineno,
                    "class",
                    class_symbol,
                )
        else:
            add_source_unit(
                chunks,
                source_lines,
                file_path,
                node_start(node),
                node.end_lineno or node.lineno,
                "module",
                node_name(node),
            )
    return chunks


def chunk_markdown(text: str, file_path: str) -> List[Chunk]:
    lines = text.splitlines()
    headings = [
        (index, len(match.group(1)), match.group(2).strip())
        for index, line in enumerate(lines)
        if (match := MARKDOWN_HEADING.match(line))
    ]
    if not headings:
        return split_lines(lines, file_path, 1, "fallback")

    chunks: List[Chunk] = []
    heading_stack: List[tuple[int, str]] = []
    section_starts = (
        ([0] if headings[0][0] > 0 else [])
        + [index for index, _, _ in headings]
    )
    section_ends = [start - 1 for start in section_starts[1:]] + [len(lines) - 1]
    headings_by_start = {index: (level, title) for index, level, title in headings}

    for start, end in zip(section_starts, section_ends):
        if start in headings_by_start:
            level, title = headings_by_start[start]
            heading_stack = [(depth, name) for depth, name in heading_stack if depth < level]
            heading_stack.append((level, title))
        symbol = " > ".join(name for _, name in heading_stack) or None
        chunks.extend(
            split_lines(
                lines[start : end + 1],
                file_path,
                start + 1,
                "markdown_section",
                symbol,
            )
        )
    return chunks


def chunk_text(text: str, file_path: str) -> List[Chunk]:
    if file_path.lower().endswith(".py"):
        return chunk_python(text, file_path)
    if file_path.lower().endswith(".md"):
        return chunk_markdown(text, file_path)
    return split_lines(text.splitlines(), file_path, 1, "fallback")


def build_repo_chunks(root: Path) -> Dict[str, object]:
    chunks: List[Chunk] = []
    for file_path in sorted(iter_source_files(root)):
        try:
            text = file_path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            print(f"Skipping {file_path}: {error}", file=sys.stderr)
            continue

        relative_path = file_path.relative_to(root).as_posix()
        chunks.extend(chunk_text(text, relative_path))

    return {
        "repository": root.name,
        "generated_from": str(root),
        "target_chunk_chars": TARGET_CHARS,
        "overlap_chars": OVERLAP_CHARS,
        "total_chunks": len(chunks),
        "chunks": chunks,
    }


def main() -> None:
    repository_chunks = build_repo_chunks(REPO_ROOT)
    OUTPUT_PATH.write_text(json.dumps(repository_chunks, indent=2), encoding="utf-8")
    print(f"Saved {repository_chunks['total_chunks']} chunks to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
