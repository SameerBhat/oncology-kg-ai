"""
OnCoPro embedding system.
"""

from .utils import (
    embed_text,
    get_embedding_model,
    split_text_into_chunks,
    embed_text_using_jina_model,
    embed_text_using_qwen3_model,
)

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
    # Main functions
    "embed_text",
    "get_embedding_model", 
    "split_text_into_chunks",
    
    # Legacy functions
    "embed_text_using_jina_model",
    "embed_text_using_qwen3_model",
    
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

__all__ = [
    # Main functions
    "embed_text",
    "get_embedding_model", 
    "split_text_into_chunks",
    
    # Legacy functions
    "embed_text_using_jina_model",
    "embed_text_using_qwen3_model",
    
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