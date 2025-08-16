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
python -m venv venv

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

TO generate embeddings from source
npm run convert-mm-db
To generate embeddings from source using current selected model in env
python generate_db_embeddings.py

##After data is annotated, run the following steps to compute metrics and generate reports:

# 1) Build curated qrels from completed answers (temporary, binary, top-R=5)
python bootstrap_qrels_from_ordered.py
```shell
qrels bootstrap done: upserts=485, updated=0, questions=21, kept=384, skipped_dup_flag=0, skipped_repeat_id=0, skipped_irrelevant=228, manually_added=0
```

# 2) Flatten answers → runs
python flatten_runs_from_answers.py
```shell
runs built: 1522 rows from 162 answers | skipped_dup_flag=0, skipped_repeat_id=0, manually_added=0, DROP_DUPLICATES=on
```

# 3) Compute metrics (CSV outputs in metrics_out/)
python compute_metrics.py
```shell
[INFO] Loaded 485 qrels rows across 21 questions.
[INFO] Loaded runs: 1522 rows -> 1522 kept after de-dup.
[INFO] Models found: 6
[OK] Wrote metrics_out/model_summary.csv
[OK] Wrote metrics_out/per_query_metrics.csv
[OK] Wrote metrics_out/per_query_ndcg10.csv
[DONE] Metrics computed
```

# 4) (Optional) Significance tests
python wilcoxon_significance.py
```shell
[OK] wrote tables/wilcoxon_ndcg10.csv and tables/wilcoxon_ndcg10.md
```

python plot_ir_figures.py 
```shell
[INFO] metrics_out/efficiency.csv not found; skipping latency figure.
```
python make_tables.py
```shell
[OK] Wrote tables/model_table.md and .tex
```
python generate_case_studies.py
```shell
FAIL
```