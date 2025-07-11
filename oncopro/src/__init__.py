"""
OnCoPro embedding system.
"""

from .embeddings import (
    EmbeddingModel,
    EmbeddingModelFactory,
    JinaEmbedding,
    QwenEmbedding,
    OpenAIEmbedding,
    get_device,
)

from .config import (
    MAX_TOKENS,
    MAX_WORDS,
    MONGO_URI,
    DATABASE_NAME,
    EMBEDDING_MODEL,
)

__all__ = [
    # Classes
    "EmbeddingModel",
    "EmbeddingModelFactory",
    "JinaEmbedding",
    "QwenEmbedding", 
    "OpenAIEmbedding",
    
    # Utilities
    "get_device",
    
    # Configuration
    "MAX_TOKENS",
    "MAX_WORDS",
    "MONGO_URI",
    "DATABASE_NAME",
    "EMBEDDING_MODEL",
]