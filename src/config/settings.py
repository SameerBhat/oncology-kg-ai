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
# Database name is based on the embedding model being used
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "jina4")  # Default to jina4
DATABASE_NAME = EMBEDDING_MODEL  # Use model name as database name

# Hardware configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 5
