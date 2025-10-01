# GRAG Integration Overview

This document explains how GRAG-style graph retrieval replaces the previous
brute-force cosine search inside **oncology-kg-ai**.

## Goals

- Surface nodes that are relevant both semantically **and** structurally
- Reuse the existing MongoDB schema without backfilling changes
- Keep legacy entrypoints (`cosine_search`, CLI scripts, tests) working
- Provide deterministic, inspectable metadata for downstream answer pipelines

## High-level Architecture

```
MongoDB (nodes collection)
│
├─ GraphIndex
│   ├─ Node cache (embeddings, text fields)
│   ├─ NetworkX graph for parent/child/linked relations
│   └─ Edge relation catalogue
│
└─ GragRetriever
    ├─ Query embedding (existing embed_text())
    ├─ Seed selection (top-k cosine seeds)
    ├─ k-hop subgraph expansion with hop decay
    ├─ Score blending (node vs subgraph weights)
    └─ Graph context enrichment (seed, hop, neighbours)
```

`SearchManager` now delegates to `GragRetriever`, so all Python callers and CLI
entry points gain the new behaviour transparently.

## Scoring Pipeline

1. Embed the query using the active embedding model
2. Pick `seed_top_k` nodes with the highest cosine similarity
3. For each seed, collect nodes within `hops` graph distance
4. Compute a subgraph representation (mean of member embeddings)
5. Blend direct node similarity and subgraph similarity using
   `node_weight` / `subgraph_weight`
6. Apply a geometric `hop_decay` so distant nodes contribute less
7. Attach graph metadata (seed node, hop distance, neighbour relations)
8. Filter by threshold and return the top-k nodes

## Configuration

`GragConfig` exposes the main levers:

| Field | Meaning |
|-------|---------|
| `hops` | Maximum hop distance explored from each seed |
| `seed_top_k` | Seeds expanded per query |
| `candidate_multiplier` | Over-fetch factor before trimming to `top_k` |
| `node_weight` / `subgraph_weight` | Balance between local and structural signals |
| `hop_decay` | Factor applied per hop (0–1) |
| `cache_ttl_seconds` | Time-to-live for the cached graph index |
| `max_context_neighbors` | Number of neighbours surfaced in responses |

Tune by constructing a `GragConfig` and passing it to `SearchManager`.

## Data Compatibility

- Nodes without embeddings are skipped automatically (as before)
- Edge extraction understands both `ObjectId` and string references
- All additional metadata is appended under `graph_context` so existing
  consumers that ignore the new field continue to function
- Answer generation now persists `graph_context` alongside each node match

## Operational Considerations

- The graph index rebuilds lazily and honours `cache_ttl_seconds`
- Use `SearchManager.refresh_index(force=True)` after bulk updates
- `get_search_stats()` reports graph size, embedding dimension, and the last
  rebuild timestamp to assist with monitoring / alerting

## Testing

- `python -m compileall src/retrieval/grag.py src/search.py` ensures syntax validity
- Existing integration tests continue to call the public API without changes

For further usage examples, see `SEARCH_README.md`, `search.py`, and
`search_advanced.py`.
