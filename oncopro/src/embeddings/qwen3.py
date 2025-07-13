"""
Qwen3 embedding model implementation.
"""
from typing import Dict, Any, List, Optional

from sentence_transformers import SentenceTransformer

from .base import EmbeddingModel


class Qwen3Embedding(EmbeddingModel):
    """Qwen3 embedding model implementation."""
    
    # Model configuration - all in one place!
    MODEL_ID = "qwen3"
    MODEL_NAME = "Qwen/Qwen3-Embedding-4B"
    MAX_SEQ_LENGTH = 32768
    
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "model_name": self.MODEL_NAME,
            "trust_remote_code": True,
            "model_kwargs": {"device_map": "auto"},
            "tokenizer_kwargs": {"padding_side": "left"},
            "max_seq_length": self.MAX_SEQ_LENGTH
        }
    
    def load_model(self) -> None:
        config = self.get_model_config()
        self.model = SentenceTransformer(
            config["model_name"],
            trust_remote_code=config["trust_remote_code"],
            model_kwargs=config["model_kwargs"],
            tokenizer_kwargs=config["tokenizer_kwargs"]
        )
        self.model.max_seq_length = config["max_seq_length"]
