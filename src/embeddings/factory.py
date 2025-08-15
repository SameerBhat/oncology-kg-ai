"""
Factory for creating embedding models.
"""
from typing import List, Dict, Type

from .base import EmbeddingModel
from .jina4 import Jina4Embedding
from .openai import OpenAIEmbedding
from .qwen34B import Qwen34BEmbedding
from .nvembedv2 import NVEmbedV2
from .bgem3 import BGEM3Embedding
from .mpnetbase2 import MPNetBase2Embedding
from .gte import GTEMultilingualBaseEmbedding
from .nomicv2 import NomicV2Embedding


class EmbeddingModelFactory:
    """Factory class for creating embedding models."""
    
    # Auto-discover models from imported classes, N
    _model_classes = [
        Jina4Embedding, Qwen34BEmbedding, BGEM3Embedding, GTEMultilingualBaseEmbedding,


       MPNetBase2Embedding, ## don know
        NomicV2Embedding, # didnt try I guess, 768 dimensions, -----------
        NVEmbedV2, # very heavy model, dimensions were 4096, couldnt handle it
        OpenAIEmbedding # paid
    ]
    
    @classmethod
    def _get_models_registry(cls) -> Dict[str, Type[EmbeddingModel]]:
        """Build the models registry from available model classes."""
        return {model_cls.MODEL_ID: model_cls for model_cls in cls._model_classes}
    
    @classmethod
    def create_model(cls, model_name: str, **kwargs) -> EmbeddingModel:
        """Create an embedding model by name."""
        models = cls._get_models_registry()
        if model_name not in models:
            available_models = ", ".join(models.keys())
            raise ValueError(f"Unknown model '{model_name}'. Available models: {available_models}")
        
        return models[model_name](**kwargs)
    
    @classmethod
    def register_model(cls, model_class: Type[EmbeddingModel]) -> None:
        """Register a new embedding model class."""
        if not issubclass(model_class, EmbeddingModel):
            raise ValueError(f"Model class must inherit from EmbeddingModel")
        
        # Check if model already exists
        for existing_model in cls._model_classes:
            if existing_model.MODEL_ID == model_class.MODEL_ID:
                raise ValueError(f"Model with ID '{model_class.MODEL_ID}' already registered")
        
        cls._model_classes.append(model_class)
    
    @classmethod
    def list_available_models(cls) -> List[str]:
        """List all available model names."""
        return list(cls._get_models_registry().keys())
    
    @classmethod
    def list_available_model_names(cls) -> List[str]:
        """List all available model names (actual model identifiers)."""
        return [model_cls.MODEL_NAME for model_cls in cls._model_classes]
    
    @classmethod
    def get_model_info(cls, model_name: str) -> Dict[str, str]:
        """Get information about a specific model."""
        models = cls._get_models_registry()
        if model_name not in models:
            raise ValueError(f"Unknown model '{model_name}'")
        
        model_cls = models[model_name]
        return {
            "id": model_cls.MODEL_ID,
            "name": model_cls.MODEL_NAME,
            "max_seq_length": str(model_cls.MAX_SEQ_LENGTH)
        }
