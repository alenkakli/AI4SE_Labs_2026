# Embedding Matching Design

## Chosen approach

`match_embeddings.py` ranks stored repository chunks by cosine similarity to a
query embedding and returns the top *k* matches, including each chunk's file,
symbol, line range, score, and a short text preview. Run it with a task
description and optionally set `--top-k` or `--store`.

The script also exposes `retrieve_top_matches` for callers that already have a
query vector, and `retrieve_for_query` for task descriptions. For text queries,
it rebuilds the Task 3 TF-IDF vocabulary from the text retained in the embedding
store, using the same vectorizer settings. It checks that the reconstructed
vectors match the stored vectors before using the query vector, preventing
comparisons between incompatible feature spaces.

## Design decisions

- **Cosine similarity** measures direction rather than vector magnitude, which
  suits the L2-normalized TF-IDF vectors created in Task 3.
- **Stored vectors are used for ranking.** They are loaded from the Task 3
  output rather than regenerated as the retrieval result set.
- **The top-*k* count is configurable** and defaults to five; equal scores retain
  the original chunk order for deterministic output.
- **Input data and dimensions are validated** so malformed stores, incompatible
  query vectors, and empty queries fail explicitly instead of returning
  misleading matches.
