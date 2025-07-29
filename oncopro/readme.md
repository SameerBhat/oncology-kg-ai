# OncroPro Embedding System

A flexible, modular embedding system that supports multiple embedding models with easy switching capabilities.

## 🚀 Quick Start

1. **Install dependencies:**

   ```bash
   npm install
   pip install -r requirements.txt
   ```

2. **Configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env to set EMBEDDING_MODEL and DATABASE_URI
   ```

3. **Add your data:**

   ```bash
   # Place mindmap (.mm) and category (.csv) files in data/ directory
   ```

4. **Generate embeddings:**
   ```bash
   npm run convert-mm-db
   python generate_db_embeddings.py
   ```

## 📦 Available Models

- **jina4** - Jina AI embeddings v4 (8192 max tokens)
- **qwen3** - Qwen3 embedding model (32768 max tokens)
- **openai** - OpenAI text embeddings (8192 max tokens)

Each model is self-contained with its own configuration.

## 📁 Project Structure

```
├── src/                     # Source code
│   ├── config/             # Configuration management
│   ├── database/           # Database operations
│   ├── embeddings/         # Embedding model implementations
│   └── utils.py            # Utility functions
├── tests/                  # Test files
├── tools/                  # Utility scripts
├── data/                   # Data files (mindmaps, CSVs)
├── docs/                   # Documentation
├── generate_db_embeddings.py  # Main embedding generation script
└── tree-parser.ts          # TypeScript mindmap parser
```

## 📖 Documentation

- [Quick Start Guide](HOW_TO.md) - Step-by-step usage instructions
- [Architecture](docs/CENTRALIZED_CONFIG.md) - Centralized configuration design

## 🧪 Testing

```bash
python -m pytest tests/
```

## 🔧 Tools

- `tools/db_manager.py` - Database management and statistics

## 🤝 Contributing

1. Each embedding model is self-contained in `src/embeddings/`
2. Add tests in `tests/`
3. Update documentation as needed

## 📄 License

ISC
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
├── **init**.py # Public API
├── utils.py # High-level utility functions
├── config/ # Configuration management
│ ├── **init**.py
│ └── settings.py
└── embeddings/ # Model implementations
├── **init**.py
├── base.py # Abstract base class
├── factory.py # Model factory
├── jina.py # Jina AI implementation
├── qwen.py # Qwen3 implementation
└── openai.py # OpenAI implementation

````

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
````

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
python generate_db_embeddings.py
npm run convert-mm-db
