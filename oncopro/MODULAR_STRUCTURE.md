# Modular Embedding System

## Overview

The embedding system has been refactored into a clean, modular architecture that separates concerns and makes the code easier to maintain, test, and extend.

## Project Structure

```
src/
├── __init__.py              # Main exports and public API
├── utils.py                 # High-level utility functions
├── config/                  # Configuration management
│   ├── __init__.py
│   └── settings.py          # Environment variables and constants
└── embeddings/              # Embedding models
    ├── __init__.py
    ├── base.py              # Abstract base class
    ├── factory.py           # Model factory
    ├── jina.py              # Jina embedding implementation
    ├── qwen.py              # Qwen embedding implementation
    └── openai.py            # OpenAI embedding implementation (placeholder)
```

## Key Components

### 1. Configuration (`src/config/`)

- **`settings.py`**: Contains all configuration constants and environment variables
- Centralized configuration management
- Easy to modify model parameters and settings

### 2. Embedding Models (`src/embeddings/`)

- **`base.py`**: Abstract base class `EmbeddingModel` defining the interface
- **`jina.py`**: Jina AI embedding model implementation
- **`qwen.py`**: Qwen3 embedding model implementation
- **`openai.py`**: OpenAI embedding model (placeholder for future implementation)
- **`factory.py`**: Factory pattern for creating model instances

### 3. Utilities (`src/utils.py`)

- High-level functions for embedding operations
- Global model management
- Text processing utilities
- Backward compatibility functions

## Usage

### Basic Usage

```python
from src import embed_text, EmbeddingModelFactory

# Simple embedding with default model
embedding = embed_text("Your text here")

# Specify model explicitly
embedding = embed_text("Your text here", model_name="jina")

# List available models
models = EmbeddingModelFactory.list_available_models()
print(f"Available: {models}")
```

### Advanced Usage

```python
from src import get_embedding_model, EmbeddingModel

# Get model instance for batch processing
model = get_embedding_model("jina")
chunks = ["text 1", "text 2", "text 3"]
embeddings = model.encode_chunks(chunks)

# Create custom model
class CustomEmbedding(EmbeddingModel):
    def get_model_config(self):
        return {"model_name": "custom-model", "max_seq_length": 512}

    def load_model(self):
        # Your implementation here
        pass

# Register and use
EmbeddingModelFactory.register_model("custom", CustomEmbedding)
embedding = embed_text("test", model_name="custom")
```

### Configuration

Set environment variables in your `.env` file:

```bash
EMBEDDING_MODEL=jina          # Choose default model
DATABASE_URI=mongodb://...    # Database connection
```

## Benefits of Modular Structure

### 1. **Separation of Concerns**

- Configuration isolated in `config/`
- Each model has its own file
- Clear boundaries between components

### 2. **Easy Testing**

- Each module can be tested independently
- Mock individual components easily
- Clear dependencies

### 3. **Extensibility**

- Add new models by creating new files in `embeddings/`
- Register models with the factory
- No need to modify existing code

### 4. **Maintainability**

- Small, focused files
- Clear import structure
- Easy to find and fix issues

### 5. **Reusability**

- Import only what you need
- Use individual components in different contexts
- Clean public API

## Migration from Old Code

The refactor maintains full backward compatibility:

```python
# Old way (still works)
from src.utils import embed_text_using_jina_model
embedding = embed_text_using_jina_model("text")

# New way (recommended)
from src import embed_text
embedding = embed_text("text", model_name="jina")
```

## Adding New Models

1. Create a new file in `src/embeddings/` (e.g., `new_model.py`)
2. Inherit from `EmbeddingModel`
3. Implement required methods
4. Register with the factory
5. Add to `__init__.py` exports

Example:

```python
# src/embeddings/new_model.py
from .base import EmbeddingModel

class NewModelEmbedding(EmbeddingModel):
    def get_model_config(self):
        return {"model_name": "new-model", "max_seq_length": 1024}

    def load_model(self):
        # Implementation here
        pass

# Register in your code
from src.embeddings import EmbeddingModelFactory
EmbeddingModelFactory.register_model("new", NewModelEmbedding)
```

## Testing

Run the test script to verify everything works:

```bash
python test_modular.py
```

## Files Created/Modified

### New Files:

- `src/config/__init__.py` - Configuration module exports
- `src/config/settings.py` - Configuration constants
- `src/embeddings/__init__.py` - Embedding module exports
- `src/embeddings/base.py` - Abstract base class
- `src/embeddings/factory.py` - Model factory
- `src/embeddings/jina.py` - Jina implementation
- `src/embeddings/qwen.py` - Qwen implementation
- `src/embeddings/openai.py` - OpenAI placeholder
- `test_modular.py` - Test script

### Modified Files:

- `src/__init__.py` - Updated exports
- `src/utils.py` - Cleaned up, now only high-level functions
- `src/utils_old.py` - Backup of original utils.py

The new structure is cleaner, more maintainable, and easier to extend while maintaining full backward compatibility.
