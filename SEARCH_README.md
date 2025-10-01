# Search System Documentation

The search stack now uses a Graph Retrieval-Augmented Generation (GRAG) strategy
that couples semantic similarity with the structural topology of the
OnCoPro/Oncology knowledge graph.  Each query produces a query-aware subgraph
around the most relevant seed nodes, providing better contextual grounding than
brute-force cosine matching.

## Overview

When you change the `EMBEDDING_MODEL` in `.env`, the search system will:

1. Connect to the database named after the embedding model
2. Use that model for query embeddings
3. Retrieve candidates through GRAG, blending node similarity and subgraph
   relevance
4. Return node-level payloads enriched with graph context (seed node, hop
   distance, neighbouring relations)

## Quick Start

### 1. Interactive Search

```bash
python search.py
```

The CLI mirrors the original workflow and now prints the graph provenance for
each hit.

### 2. Advanced Modes

```bash
python search_advanced.py --mode interactive
```

Available modes:

- `interactive`: enhanced console UI with model hints and graph context
- `batch`: run multiple queries and capture aggregated metrics
- `similarity`: fetch nodes similar to an existing `nodeid`
- `stats`: show search/index statistics, including graph size

### 3. One-off Query

```bash
python search_advanced.py --query "your search query" --top-k 10
```

## Model Configuration

Recommended parameters remain compatible with the previous system:

| Model      | Top-k | Threshold | Notes                                                    |
|------------|-------|-----------|----------------------------------------------------------|
| `jina4`    | 10    | 0.30      | Balanced for longer/multilingual queries                 |
| `qwen34b`  | 8     | 0.25      | Strong for technical and multilingual content            |
| `bgem3`    | 7     | 0.20      | Optimised for multilingual & cross-lingual retrieval     |
| `nvembedv2`| 5     | 0.40      | Best with English content, benefits from higher thresholds|
| `openai`   | 10    | 0.30      | General-purpose baseline                                 |

## Database Expectations

Nodes are stored in MongoDB with the existing schema produced by the ingestion
pipeline.  The retriever consumes the following fields (additional fields are
preserved pass-through):

```json
{
  "_id": ObjectId("..."),
  "nodeid": "unique-node-id",
  "text": "Primary label",
  "richText": "Long form description or HTML",
  "notes": "Free-form notes",
  "links": ["https://..."],
  "attributes": [{"name": "Status", "value": "Approved"}],
  "embedding": [0.1, 0.2, ...],
  "parentID": ObjectId("..."),
  "children": [ObjectId("...")],
  "linkedNodes": [ObjectId("...")]
}
```

Edges are derived from `parentID`, `children`, and `linkedNodes`, then cached in
memory for fast GRAG retrieval.

## Programming Interface

```python
from src import MongoDBClient, SearchManager

with MongoDBClient() as db_client:
    search_manager = SearchManager(db_client)
    results = search_manager.search("targeted therapy", top_k=5)
```

To pin a specific embedding model/database:

```python
with MongoDBClient(database_name="jina4") as db_client:
    search_manager = SearchManager(db_client, embedding_model_name="jina4")
    results = search_manager.search("angiogenesis", top_k=5)
```

## Search Methods

```python
# Graph-aware search
results = search_manager.search(
    query="precision oncology",
    top_k=5,
    threshold=0.1,
)

# Historical alias (still available)
legacy = search_manager.cosine_search("precision oncology", top_k=5)

# Find neighbours for an existing node
similar = search_manager.get_similar_nodes(
    node_id="NODE_ID",
    top_k=5,
    exclude_self=True,
)

# Batch queries
batch_results = search_manager.batch_search(
    queries=["immune checkpoint", "tumour microenvironment"],
    top_k=5,
)

# Retrieve stats (includes graph and embedding metadata)
stats = search_manager.get_search_stats()
```

## Result Payload

Each hit includes the node information alongside GRAG metadata:

```python
{
    "nodeid": "NODE_123",
    "id": "64f...",
    "text": "VEGF signalling",
    "richText": "Longer description...",
    "notes": "Clinical trial evidence...",
    "links": ["https://example.org"],
    "attributes": [{"name": "Phase", "value": "III"}],
    "score": 0.78,
    "graph_context": {
        "seed_node": "NODE_045",
        "hop_distance": 1,
        "subgraph_score": 0.81,
        "local_similarity": 0.75,
        "neighbors": [
            {"nodeid": "NODE_200", "relations": ["hierarchy"]},
            {"nodeid": "NODE_265", "relations": ["link"]}
        ]
    }
}
```

Persisted answer documents automatically store the `graph_context` so downstream
pipelines retain visibility into the retrieval rationale.

## Similarity Mode

`get_similar_nodes` now composes a synthetic query from the node's textual
fields and runs GRAG search.  This keeps behaviour consistent with prior cosine
matching while benefiting from graph-structured retrieval.

## Monitoring the Index

`search_manager.refresh_index(force=True)` forces a rebuild of the in-memory
cache.  The cache automatically refreshes based on `GragConfig.cache_ttl_seconds`
(15 minutes by default).  `get_search_stats()` reports:

- total nodes in the MongoDB collection
- nodes included in the indexed graph (i.e. with embeddings)
- edges captured in the graph index
- embedding dimensionality and last rebuild timestamp

## Customising GRAG Parameters

Pass a `GragConfig` instance to `SearchManager` to tune behaviour:

```python
from src import GragConfig, SearchManager

config = GragConfig(hops=3, seed_top_k=32, node_weight=0.7, subgraph_weight=0.3)
search_manager = SearchManager(grag_config=config)
```

Configuration fields:

- `hops`: number of hops explored from each seed node
- `seed_top_k`: seeds expanded per query
- `node_weight` / `subgraph_weight`: balance between direct similarity and
graph context
- `hop_decay`: geometric decay applied as distance from the seed increases
- `max_context_neighbors`: how many neighbours are surfaced in the response
- `cache_ttl_seconds`: lifespan of the cached index (set `None` to disable TTL)

Enjoy deeper, structure-aware retrieval across the Oncology knowledge graph!
