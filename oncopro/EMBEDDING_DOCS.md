# Embedding System Documentation

## Overview

The embedding system has been refactored to provide a flexible, extensible architecture for switching between different embedding models. The system uses a factory pattern with abstract base classes to make adding new models easy.

## Supported Models

- **jina**: Jina AI embeddings v4 (8192 token context)
- **qwen/qwen3**: Qwen3 embedding models (32k token context)
- **openai**: OpenAI embeddings (placeholder - needs API implementation)

## Quick Start

### 1. Set Environment Variable

Add to your `.env` file:

```bash
EMBEDDING_MODEL=jina  # or qwen, qwen3, openai
```

### 2. Basic Usage

```python
from src.utils import embed_text, get_embedding_model

# Simple embedding
embedding = embed_text("Your text here")

# Specify model explicitly
embedding = embed_text("Your text here", model_name="jina")

# For Qwen models, use prompt_name for queries
query_embedding = embed_text("What is this about?", model_name="qwen", prompt_name="query")
```

### 3. Advanced Usage

```python
from src.utils import EmbeddingModelFactory, get_embedding_model

# List available models
models = EmbeddingModelFactory.list_available_models()
print(f"Available: {models}")

# Get model instance for batch processing
model = get_embedding_model("jina")
chunks = ["text 1", "text 2", "text 3"]
embeddings = model.encode_chunks(chunks)
```

## Adding Custom Models

```python
from src.utils import EmbeddingModel, EmbeddingModelFactory

class MyCustomEmbedding(EmbeddingModel):
    def get_model_config(self):
        return {
            "model_name": "your-model-name",
            "max_seq_length": 512,
            # ... other config
        }

    def load_model(self):
        config = self.get_model_config()
        self.model = SentenceTransformer(config["model_name"])
        self.model.max_seq_length = config["max_seq_length"]

# Register your model
EmbeddingModelFactory.register_model("custom", MyCustomEmbedding)

# Use it
embedding = embed_text("test", model_name="custom")
```

## Configuration Options

Set these in your `.env` file:

```bash
EMBEDDING_MODEL=jina          # Default model to use
DATABASE_URI=mongodb://...    # MongoDB connection
```

## Migration from Old Code

The refactor maintains backward compatibility:

```python
# Old way (still works)
from src.utils import embed_text_using_jina_model
embedding = embed_text_using_jina_model("text")

# New way (recommended)
from src.utils import embed_text
embedding = embed_text("text", model_name="jina")
```

## Error Handling

The system includes robust error handling with retry logic for transient errors (rate limits, network issues). Models are loaded lazily on first use.

## Performance Notes

- Models are cached globally - only loaded once per process
- Supports GPU acceleration (CUDA/MPS) when available
- Automatic batching for chunk processing
- Mean pooling for long documents that exceed context length

## Installation

Install additional dependencies:

```bash
pip install -r requirements.txt
```

Required packages:

- sentence-transformers
- torch
- peft (for Jina models)
- accelerate
- transformers>=4.21.0
