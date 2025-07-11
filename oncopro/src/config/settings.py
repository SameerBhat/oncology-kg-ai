"""
Configuration settings for the embedding system.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Token and chunking configuration
MAX_TOKENS = 8192
AVG_WORDS_PER_TOKEN = 0.75
MAX_WORDS = int(MAX_TOKENS / AVG_WORDS_PER_TOKEN)

# Database configuration
MONGO_URI = os.getenv("DATABASE_URI", "mongodb://localhost:27017")
DATABASE_NAME = "oncopro"

# Embedding model configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "jina")  # Default to jina

# Model-specific configurations
JINA_MODEL_NAME = "jinaai/jina-embeddings-v4"
JINA_MAX_SEQ_LENGTH = 8192

QWEN_MODEL_NAME = "Qwen/Qwen3-Embedding-4B"
QWEN_MAX_SEQ_LENGTH = 32768

OPENAI_MODEL_NAME = "text-embedding-3-large"
OPENAI_MAX_SEQ_LENGTH = 8192

# Hardware configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 5
