# Chunk Embeddings Design

## Chosen approach

I implemented a TF-IDF embedding strategy for each repository chunk and stored the chunk-plus-vector pairs in a JSON file.

Why this choice:
- TF-IDF is a standard bag-of-words embedding that converts text into a fixed-length numerical vector.
- It is deterministic, fast, and does not rely on external model downloads or GPU resources.
- It works well for local retrieval tasks where the goal is to find chunks whose vocabulary overlaps with the user request.
- It produces a compact vector representation that is easy to store and compare with cosine similarity.

## What is embedded

I embed only the chunk payload (`chunk["text"]`). I do not include the file path or raw metadata in the vector because the path and symbol names are useful as identifiers, but they carry less semantic meaning than the actual code or prose content. For code-heavy repository search, the text itself should dominate similarity.

## Storage design

The output file stores:
- chunk id
- file path
- kind and symbol metadata
- source line range
- the original text
- the generated embedding vector

This keeps the data easy to inspect and allows downstream retrieval by file, symbol, or semantic similarity.

## Retrieval design

The same script can compare a query string against the stored chunk vectors using cosine similarity. This is a standard and interpretable retrieval metric for sparse embeddings like TF-IDF.

## Why this is a good fit for this project

The repository is already chunked into meaningful units in Task 2. TF-IDF on those chunks gives a lightweight but practical retrieval layer without introducing a heavy dependency or a brittle runtime setup. It is a good compromise between simplicity, reproducibility, and usefulness for later RAG or code-search workflows.
