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

from .embedding_utils import (
    setup_logging,
    log_progress,
    log_embedding_stats,
    ProgressTracker,
)

from .database import (
    MongoDBClient,
    NodesManager,
    NodeDocument,
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
    
    # Database classes
    "MongoDBClient",
    "NodesManager",
    "NodeDocument",
    
    # Utility functions
    "setup_logging",
    "log_progress", 
    "log_embedding_stats",
    "ProgressTracker",
    
    # Utilities
    "get_device",
    
    # Configuration
    "MAX_TOKENS",
    "MAX_WORDS",
    "MONGO_URI",
    "DATABASE_NAME",
    "EMBEDDING_MODEL",
]