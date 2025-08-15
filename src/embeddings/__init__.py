"""
Embedding models module.
"""

from .base import EmbeddingModel, get_device
from .jina4 import Jina4Embedding
from .qwen34B import Qwen34BEmbedding
from .openai import OpenAIEmbedding
from .nomicv2 import NomicV2Embedding
from .factory import EmbeddingModelFactory

__all__ = [
    "EmbeddingModel",
    "get_device",
    "Jina4Embedding",
    "Qwen34BEmbedding",
    "OpenAIEmbedding",
    "NomicV2Embedding",
    "EmbeddingModelFactory",
]
