"""
Configuration module for the embedding system.
"""

from .settings import (
    MAX_TOKENS,
    AVG_WORDS_PER_TOKEN,
    MAX_WORDS,
    MONGO_URI,
    DATABASE_NAME,
    EMBEDDING_MODEL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_DELAY,
)

__all__ = [
    "MAX_TOKENS",
    "AVG_WORDS_PER_TOKEN", 
    "MAX_WORDS",
    "MONGO_URI",
    "DATABASE_NAME",
    "EMBEDDING_MODEL",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_RETRY_DELAY",
]
