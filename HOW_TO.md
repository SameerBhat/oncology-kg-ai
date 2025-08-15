# Embedding Generation Guide

This project enables the generation of embeddings from a mindmap structure using various models.

## 📦 Available Models

> **Note**: Each model defines its own configuration in the respective class file in [`src/embeddings/`](src/embeddings/)

- `jina4` - Jina AI embeddings v4 (8192 max tokens)
- `qwen3` - Qwen3 embedding model (32768 max tokens)
- `openai` - OpenAI text embeddings (8192 max tokens)

## 🧠 Prerequisites

- Ensure the mindmap file is present in the `data/` directory
- Verify that the `"convert-mm-db"` script in `package.json` properly references the mindmap file
- Define the embedding model by setting the `EMBEDDING_MODEL` variable in your `.env` file

## ⚙️ How to Generate Embeddings

1. **Prepare the mindmap:**

   - Place the mindmap file in the `data/` directory
   - Ensure the `package.json` script `"convert-mm-db"` correctly references this file

2. **Set the embedding model:**

   - In your `.env` file, specify the model to use:
     ```env
     EMBEDDING_MODEL=qwen3  # or jina4, openai
     ```
   - The name of the model will also be the name of the database that will be created

3. **Generate the initial database:**
   Run the following command:

   ```bash
   npm run convert-mm-db
   ```

   - This will generate a database named after the selected `EMBEDDING_MODEL`
   - Check that the `nodes` collection exists and contains data

4. **Verify the generated data:**

   - Inspect the `nodes` collection to see if the `embeddings` field exists
   - If `embeddings` is missing for a node, embeddings have not been generated yet

5. **Generate embeddings using Python:**
   Run the following command:
   ```bash
   python generate_db_embeddings.py
   ```
   - This script reads the `EMBEDDING_MODEL` environment variable to determine which database to target
   - It only processes nodes that do **not** have embeddings, so you can run this script safely multiple times

## 🔁 Regenerating Embeddings

The `generate_db_embeddings.py` script is idempotent — running it multiple times will only generate embeddings for nodes that are missing them. Existing embeddings will not be overwritten.

## 📁 Project Structure

```
├── src/                     # Source code
│   ├── config/             # Configuration management
│   ├── database/           # Database operations
│   ├── embeddings/         # Embedding model implementations
│   └── utils.py            # Utility functions
├── tests/                  # Test files
├── data/                   # Data files (mindmaps, CSVs)
├── docs/                   # Documentation
├── generate_db_embeddings.py  # Main embedding generation script
└── tree-parser.ts          # TypeScript mindmap parser
```

## 🧪 Testing

Run tests from the project root:

```bash
python -m pytest tests/
```

---

**TLDR:**

- Place mindmap file in `data/` directory
- Set `EMBEDDING_MODEL` in `.env`
- Run: `npm run convert-mm-db`
- Run: `python3 generate_db_embeddings.py`
