# Search System Documentation

This search system provides comprehensive cosine similarity search capabilities across different embedding models in your OnCoPro project.

## Overview

The search system automatically integrates with your existing model factory and database setup. When you change the `EMBEDDING_MODEL` in your `.env` file, the search system will:

1. Connect to the corresponding database (named after the model)
2. Use that model for generating query embeddings
3. Apply model-specific search optimizations

## Quick Start

### 1. Basic Interactive Search

```bash
python search.py
```

This starts an interactive search session where you can:

- Enter search queries
- Specify number of results (top_k)
- Set similarity thresholds
- See formatted results with scores

### 2. Advanced Search Options

```bash
python search_advanced.py --mode interactive
```

Advanced modes available:

- `--mode interactive`: Interactive search with model-specific recommendations
- `--mode batch`: Search multiple queries at once
- `--mode similarity`: Find nodes similar to a specific node
- `--mode stats`: Show database and search statistics

### 3. Quick Single Query

```bash
python search_advanced.py --query "your search query" --top-k 10
```

### 4. Batch Search

```bash
python search_advanced.py --mode batch --queries "query1" "query2" "query3"
```

### 5. Similarity Search

```bash
python search_advanced.py --mode similarity --node-id "NODE_ID_HERE"
```

## Model Configuration

Each embedding model has specific configurations that optimize search performance:

### Jina4 (jina4)

- **Recommended top_k**: 10
- **Recommended threshold**: 0.3
- **Notes**: Performs well with longer queries and multilingual content

### Qwen34B (qwen34b)

- **Recommended top_k**: 8
- **Recommended threshold**: 0.25
- **Notes**: Good for technical and multilingual content

### BGE-M3 (bgem3)

- **Recommended top_k**: 7
- **Recommended threshold**: 0.2
- **Notes**: Optimized for multilingual and cross-lingual retrieval

### NVIDIA EmbedV2 (nvembedv2)

- **Recommended top_k**: 5
- **Recommended threshold**: 0.4
- **Notes**: Works best with English content, may need higher thresholds

### OpenAI (openai)

- **Recommended top_k**: 10
- **Recommended threshold**: 0.3
- **Notes**: Well-balanced for most use cases

## Database Structure

The search system expects nodes in MongoDB with the following structure:

```json
{
  "_id": ObjectId("..."),
  "content": "Text content of the node",
  "embedding": [0.1, 0.2, 0.3, ...], // Vector embedding
  "metadata": {
    "source": "optional metadata",
    "category": "optional category"
  }
}
```

## Switching Models

To switch between models:

1. Update your `.env` file:

   ```env
   EMBEDDING_MODEL=jina4  # or qwen34b, bgem3, etc.
   ```

2. The search system will automatically:
   - Connect to the `jina4` database
   - Use the Jina4 embedding model for queries
   - Apply Jina4-specific search optimizations

## Programming Interface

### Basic Usage

```python
from src import MongoDBClient, SearchManager

# Use current model from .env
with MongoDBClient() as db_client:
    search_manager = SearchManager(db_client)
    results = search_manager.cosine_search("your query", top_k=5)

# Use specific model
with MongoDBClient(database_name="jina4") as db_client:
    search_manager = SearchManager(db_client, embedding_model_name="jina4")
    results = search_manager.cosine_search("your query", top_k=5)
```

### Search Methods

```python
# Basic cosine similarity search
results = search_manager.cosine_search(
    query="search query",
    top_k=5,
    threshold=0.3
)

# Find similar nodes
similar = search_manager.get_similar_nodes(
    node_id="NODE_ID",
    top_k=5,
    exclude_self=True
)

# Batch search
batch_results = search_manager.batch_search(
    queries=["query1", "query2"],
    top_k=5
)

# Get search statistics
stats = search_manager.get_search_stats()
```

### Result Format

Search results are returned as:

```python
[
    {
        "_id": "node_id",
        "content": "node content",
        "metadata": {...},
        "score": 0.85,
        "model_used": "jina4"
    },
    ...
]
```

## Model-Specific Features

The search system includes model-specific optimizations:

### Query Preprocessing

- Different models may benefit from different query formatting
- Automatic query preprocessing based on model type

### Similarity Calculation

- Most models use cosine similarity
- Framework allows for model-specific similarity metrics
- Future support for different distance metrics

### Search Configuration

- Model-specific recommended parameters
- Automatic threshold and top_k suggestions
- Performance optimizations per model

## Examples

### Demo Script

Run the demo to see all features:

```bash
python demo_search.py
```

This demonstrates:

- Search with current model
- Model switching capabilities
- Advanced search features
- Batch and similarity search

### Example Searches

```bash
# Medical content search
python search_advanced.py --query "symptoms and diagnosis" --top-k 5

# Technical content search
python search_advanced.py --query "treatment protocols" --threshold 0.3

# Batch medical search
python search_advanced.py --mode batch --queries "symptoms" "treatment" "side effects"
```

## Performance Tips

1. **Use appropriate thresholds**: Higher thresholds filter more results but may miss relevant content
2. **Choose optimal top_k**: Balance between comprehensiveness and performance
3. **Model-specific settings**: Use the recommended settings for each model
4. **Batch processing**: Use batch search for multiple queries to improve efficiency

## Troubleshooting

### No Results Found

- Check if embeddings exist: `python search_advanced.py --mode stats`
- Run embedding generation: `python generate_db_embeddings.py`
- Lower the similarity threshold

### Model Switching Issues

- Ensure the target model database exists
- Check that embeddings were generated for that model
- Verify model name in `.env` matches available models

### Performance Issues

- Use smaller top_k values
- Increase similarity threshold to filter results
- Consider using batch search for multiple queries

## Integration with Existing Code

The search system follows your DRY and modular principles:

- **Database**: Uses your existing `MongoDBClient`
- **Models**: Integrates with your `EmbeddingModelFactory`
- **Configuration**: Respects your `.env` settings
- **Logging**: Uses your existing logging setup

No changes needed to existing code - just add search capabilities!
