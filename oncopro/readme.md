# OnCoPro Embedding System

A flexible, modular embedding system that supports multiple embedding models with easy switching capabilities.

## Features

- **Multiple Models**: Support for Jina AI, Qwen3, and OpenAI embeddings
- **Easy Switching**: Change models via environment variable or function parameter
- **Modular Design**: Clean separation of concerns for better maintainability
- **Extensible**: Add new models easily using the factory pattern
- **Backward Compatible**: Existing code continues to work unchanged

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd oncopro

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` to set your preferred embedding model:

```bash
EMBEDDING_MODEL=jina  # Options: jina, qwen, qwen3, openai
DATABASE_URI=mongodb://localhost:27017
```

### 3. Basic Usage

```python
from src import embed_text, EmbeddingModelFactory

# Simple embedding with default model
embedding = embed_text("Your text here")

# Specify model explicitly
embedding = embed_text("Your text here", model_name="jina")

# List available models
models = EmbeddingModelFactory.list_available_models()
print(f"Available models: {models}")
```

## Project Structure

```
src/
├── __init__.py              # Public API
├── utils.py                 # High-level utility functions
├── config/                  # Configuration management
│   ├── __init__.py
│   └── settings.py
└── embeddings/              # Model implementations
    ├── __init__.py
    ├── base.py              # Abstract base class
    ├── factory.py           # Model factory
    ├── jina.py              # Jina AI implementation
    ├── qwen.py              # Qwen3 implementation
    └── openai.py            # OpenAI implementation
```

## Supported Models

- **Jina AI**: `jinaai/jina-embeddings-v4` (8192 token context)
- **Qwen3**: `Qwen/Qwen3-Embedding-4B` (32k token context)
- **OpenAI**: `text-embedding-3-large` (placeholder - needs implementation)

## Adding Custom Models

```python
from src.embeddings import EmbeddingModel, EmbeddingModelFactory

class MyCustomEmbedding(EmbeddingModel):
    def get_model_config(self):
        return {"model_name": "my-model", "max_seq_length": 512}

    def load_model(self):
        # Your implementation here
        pass

# Register and use
EmbeddingModelFactory.register_model("custom", MyCustomEmbedding)
embedding = embed_text("test", model_name="custom")
```

## Documentation

- **[MODULAR_STRUCTURE.md](MODULAR_STRUCTURE.md)**: Detailed architecture documentation
- **[example_usage.py](example_usage.py)**: Comprehensive usage examples

## Development

### Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate (Unix/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Deactivate
deactivate
```

### Dependencies

```bash
# Install dependencies
pip install -r requirements.txt

# Update requirements.txt
pip freeze > requirements.txt
```

## License

MIT License
