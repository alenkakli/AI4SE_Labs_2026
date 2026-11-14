from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DEFAULT_STORE_PATH = (
    Path(__file__).resolve().parents[1]
    / "Task_3"
    / "chunk_embeddings.json"
)


def load_embedding_store(
    path: Path,
) -> tuple[list[dict[str, Any]], np.ndarray]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError(f"Expected an embedding-store object in {path}.")

    chunks = payload.get("chunks")
    dimension = payload.get("embedding_dimension")
    if not isinstance(chunks, list) or not chunks:
        raise ValueError(f"Expected a non-empty chunk list in {path}.")
    if not isinstance(dimension, int) or dimension < 1:
        raise ValueError(f"Expected a positive embedding dimension in {path}.")

    vectors: list[list[float]] = []
    for index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            raise ValueError(f"Chunk {index} in {path} is not an object.")
        vector = chunk.get("embedding")
        if not isinstance(vector, list) or len(vector) != dimension:
            raise ValueError(
                f"Chunk {index} in {path} does not have a "
                f"{dimension}-dimensional embedding."
            )
        try:
            vectors.append([float(value) for value in vector])
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Chunk {index} in {path} has a non-numeric embedding."
            ) from error

    embedding_matrix = np.asarray(vectors, dtype=float)
    if not np.isfinite(embedding_matrix).all():
        raise ValueError(f"The embedding store in {path} has non-finite values.")

    total_chunks = payload.get("total_chunks")
    if total_chunks is not None and total_chunks != len(chunks):
        raise ValueError(
            f"The chunk count in {path} does not match total_chunks."
        )

    return chunks, embedding_matrix


def build_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        max_features=256,
        sublinear_tf=True,
    )


def embed_query(
    query: str,
    chunks: list[dict[str, Any]],
) -> tuple[Any, np.ndarray]:
    texts = []
    for index, chunk in enumerate(chunks):
        text = chunk.get("text")
        if not isinstance(text, str):
            raise ValueError(f"Chunk {index} does not contain text.")
        texts.append(" ".join(text.split()))

    vectorizer = build_vectorizer()
    corpus_matrix = vectorizer.fit_transform(texts)
    query_vector = vectorizer.transform([query]).toarray()[0]
    return corpus_matrix, query_vector


def rank_matches(
    query_embedding: Sequence[float],
    chunks: list[dict[str, Any]],
    embedding_matrix: np.ndarray,
    top_k: int,
) -> list[dict[str, Any]]:
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    try:
        query_vector = np.asarray(query_embedding, dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError("The query embedding must contain numeric values.") from error

    if query_vector.ndim != 1 or query_vector.shape[0] != embedding_matrix.shape[1]:
        raise ValueError(
            "The query embedding dimension does not match the stored embeddings."
        )
    if not np.isfinite(query_vector).all():
        raise ValueError("The query embedding contains non-finite values.")
    if not np.any(query_vector):
        raise ValueError("The query embedding must not be a zero vector.")

    scores = cosine_similarity(query_vector.reshape(1, -1), embedding_matrix)[0]
    ranked_indexes = sorted(
        range(len(chunks)),
        key=lambda index: (-float(scores[index]), index),
    )[:top_k]

    matches = []
    for index in ranked_indexes:
        chunk = chunks[index]
        matches.append(
            {
                "score": float(scores[index]),
                "chunk_id": chunk.get("chunk_id"),
                "file": chunk.get("file"),
                "kind": chunk.get("kind"),
                "symbol": chunk.get("symbol"),
                "start_line": chunk.get("start_line"),
                "end_line": chunk.get("end_line"),
                "preview": str(chunk.get("text", ""))[:300],
            }
        )
    return matches


def retrieve_top_matches(
    query_embedding: Sequence[float],
    storage_path: Path = DEFAULT_STORE_PATH,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    chunks, embedding_matrix = load_embedding_store(storage_path)
    return rank_matches(query_embedding, chunks, embedding_matrix, top_k)


def retrieve_for_query(
    query: str,
    storage_path: Path = DEFAULT_STORE_PATH,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    if not query.strip():
        raise ValueError("The query must not be empty.")

    chunks, embedding_matrix = load_embedding_store(storage_path)
    corpus_matrix, query_vector = embed_query(query, chunks)

    if corpus_matrix.shape != embedding_matrix.shape or not np.allclose(
        corpus_matrix.toarray(),
        embedding_matrix,
        rtol=1e-5,
        atol=1e-8,
    ):
        raise ValueError(
            "The stored embeddings do not match the current TF-IDF settings "
            "or chunk order. Regenerate the Task 3 embeddings before retrieval."
        )

    return rank_matches(query_vector, chunks, embedding_matrix, top_k)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Retrieve the most relevant repository chunks for a task."
    )
    parser.add_argument("query", help="Task description to match against the chunks.")
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of matching chunks to return (default: 5).",
    )
    parser.add_argument(
        "--store",
        type=Path,
        default=DEFAULT_STORE_PATH,
        help="Path to the Task 3 chunk-embedding JSON file.",
    )
    args = parser.parse_args()

    matches = retrieve_for_query(args.query, args.store, args.top_k)
    print(json.dumps(matches, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
