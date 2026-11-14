from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

REPO_ROOT = Path(__file__).resolve().parents[3]
CHUNKS_PATH = REPO_ROOT / "Week_06_Implementation/Assignments/Task_2/repository_chunks.json"
OUTPUT_PATH = Path(__file__).resolve().with_name("chunk_embeddings.json")


def load_chunks(path: Path) -> List[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    chunks = payload.get("chunks", [])
    if not isinstance(chunks, list):
        raise ValueError(f"Expected a chunk list in {path}.")
    return chunks


def chunk_text(chunk: dict[str, Any]) -> str:
    text = chunk.get("text")
    if not isinstance(text, str):
        return ""
    return " ".join(text.split())


def build_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        max_features=256,
        sublinear_tf=True,
    )


def generate_embeddings() -> dict[str, Any]:
    chunks = load_chunks(CHUNKS_PATH)
    texts = [chunk_text(chunk) for chunk in chunks]

    vectorizer = build_vectorizer()
    matrix = vectorizer.fit_transform(texts)
    embeddings = matrix.toarray()

    records: List[dict[str, Any]] = []
    for index, chunk in enumerate(chunks):
        record = {
            "chunk_id": index,
            "file": chunk.get("file"),
            "kind": chunk.get("kind"),
            "symbol": chunk.get("symbol"),
            "start_line": chunk.get("start_line"),
            "end_line": chunk.get("end_line"),
            "text": chunk.get("text"),
            "embedding": [float(value) for value in embeddings[index]],
        }
        records.append(record)

    return {
        "source": str(CHUNKS_PATH.relative_to(REPO_ROOT)),
        "embedding_dimension": int(embeddings.shape[1]),
        "total_chunks": len(records),
        "chunks": records,
    }


def query_top_matches(query: str, top_k: int = 5) -> List[dict[str, Any]]:
    chunks = load_chunks(CHUNKS_PATH)
    corpus = [chunk_text(chunk) for chunk in chunks]
    vectorizer = build_vectorizer()
    matrix = vectorizer.fit_transform(corpus)
    query_vector = vectorizer.transform([query]).toarray()[0]

    similarities = cosine_similarity([query_vector], matrix.toarray())[0]
    ranked_indexes = np.argsort(similarities)[::-1][:top_k]

    matches: List[dict[str, Any]] = []
    for idx in ranked_indexes:
        chunk = chunks[int(idx)]
        matches.append(
            {
                "score": float(similarities[int(idx)]),
                "file": chunk.get("file"),
                "kind": chunk.get("kind"),
                "symbol": chunk.get("symbol"),
                "start_line": chunk.get("start_line"),
                "end_line": chunk.get("end_line"),
                "preview": chunk.get("text", "")[:300],
            }
        )
    return matches


if __name__ == "__main__":
    payload = generate_embeddings()
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(f"Saved {len(payload['chunks'])} chunk embeddings to {OUTPUT_PATH}")
