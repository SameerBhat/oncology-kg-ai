# Database Module Documentation

The database module provides a clean and modular interface for MongoDB operations in the embedding system.

## 📁 Module Structure

```
src/database/
├── __init__.py          # Module exports
├── client.py            # MongoDB connection management
├── models.py            # Data models for MongoDB documents
└── operations.py        # Database operations for nodes
```

## 🔧 Components

### MongoDBClient

Manages MongoDB connections with proper context management:

```python
from src import MongoDBClient

# Use as context manager (recommended)
with MongoDBClient() as client:
    collection = client.get_collection("nodes")
    # ... operations ...

# Or manually manage
client = MongoDBClient()
db = client.get_database()
client.close()
```

### NodeDocument

Data model representing a node document:

```python
from src import NodeDocument

# Create from dict
node = NodeDocument.from_dict(mongo_doc)

# Generate text content
text_content = node.generate_text_content()

# Check if has embedding
has_embedding = node.has_embedding()
```

### NodesManager

High-level operations for managing nodes:

```python
from src import NodesManager, MongoDBClient

with MongoDBClient() as client:
    manager = NodesManager(client)

    # Get statistics
    stats = manager.get_collection_stats()

    # Find nodes without embeddings
    for node in manager.find_nodes_without_embeddings():
        # Process node...
        pass

    # Update node with embedding
    manager.update_node_embedding(node_id, embedding_vector)
```

## 🛠️ Scripts

### generate_db_embeddings.py

Generates embeddings for all nodes that don't have them:

```bash
python generate_db_embeddings.py
```

Features:

- Uses the configured embedding model from `.env`
- Only processes nodes without embeddings
- Progress tracking with logging
- Error handling and recovery
- Database name based on embedding model

### db_manager.py

Database management utility:

```bash
# Show collection statistics
python db_manager.py --stats

# Show sample nodes with embeddings
python db_manager.py --sample-with 10

# Show sample nodes without embeddings
python db_manager.py --sample-without 5

# Clear all embeddings (with confirmation)
python db_manager.py --clear-embeddings

# Skip confirmation prompts
python db_manager.py --clear-embeddings --confirm
```

## 🎯 Key Features

1. **Modular Design**: Clean separation of concerns
2. **Context Management**: Proper resource cleanup
3. **Progress Tracking**: Detailed logging and progress bars
4. **Error Handling**: Robust error recovery
5. **Batch Operations**: Efficient bulk updates
6. **Statistics**: Comprehensive collection analytics
7. **Dynamic Database Names**: Database named after embedding model

## 📊 Statistics Tracking

The system provides detailed statistics about embedding progress:

```python
stats = nodes_manager.get_collection_stats()
# Returns:
# {
#     "total_nodes": 1000,
#     "nodes_with_embeddings": 800,
#     "nodes_without_embeddings": 200,
#     "embedding_completion_percentage": 80.0
# }
```

## 🔄 Idempotent Operations

All embedding operations are idempotent:

- Running `generate_db_embeddings.py` multiple times is safe
- Only nodes without embeddings are processed
- Existing embeddings are never overwritten

## 🗄️ Database Schema

### Node Document Structure

```javascript
{
  "_id": ObjectId("..."),
  "text": "Title text",
  "richText": "Rich text description",
  "notes": "Additional notes",
  "links": ["http://example.com"],
  "attributes": [
    {
      "name": "attribute_name",
      "value": "attribute_value"
    }
  ],
  "embedding": [0.1, 0.2, 0.3, ...] // Added by embedding process
}
```
