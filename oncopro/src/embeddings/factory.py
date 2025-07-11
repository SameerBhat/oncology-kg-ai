"""
Factory for creating embedding models.
"""
from typing import List

from .base import EmbeddingModel
from .jina import JinaEmbedding
from .qwen import QwenEmbedding
from .openai import OpenAIEmbedding


class EmbeddingModelFactory:
    """Factory class for creating embedding models."""
    
    _models = {
        "jina": JinaEmbedding,
        "qwen": QwenEmbedding,
        "qwen3": QwenEmbedding,  # Alias
        "openai": OpenAIEmbedding,
    }
    
    @classmethod
    def create_model(cls, model_name: str, **kwargs) -> EmbeddingModel:
        """Create an embedding model by name."""
        if model_name not in cls._models:
            available_models = ", ".join(cls._models.keys())
            raise ValueError(f"Unknown model '{model_name}'. Available models: {available_models}")
        
        return cls._models[model_name](**kwargs)
    
    @classmethod
    def register_model(cls, name: str, model_class: type) -> None:
        """Register a new embedding model class."""
        if not issubclass(model_class, EmbeddingModel):
            raise ValueError(f"Model class must inherit from EmbeddingModel")
        cls._models[name] = model_class
    
    @classmethod
    def list_available_models(cls) -> List[str]:
        """List all available model names."""
        return list(cls._models.keys())
