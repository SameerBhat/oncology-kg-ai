"""
Jina AI embedding model implementation.
"""
from typing import Dict, Any

from sentence_transformers import SentenceTransformer

from .base import EmbeddingModel


class Jina4Embedding(EmbeddingModel):
    """Jina AI embedding model implementation."""
    
    # Model configuration - all in one place!
    MODEL_ID = "jina4"
    MODEL_NAME = "jinaai/jina-embeddings-v4"
    MAX_SEQ_LENGTH = 8192
    
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "model_name": self.MODEL_NAME,
            "trust_remote_code": True,
            "device": self.device,
            "model_kwargs": {
                "attn_implementation": "eager",
                "default_task": "retrieval",
            },
            "max_seq_length": self.MAX_SEQ_LENGTH
        }
    
    def load_model(self) -> None:
        config = self.get_model_config()
        self.model = SentenceTransformer(
            config["model_name"],
            trust_remote_code=config["trust_remote_code"],
            device=config["device"],
            model_kwargs=config["model_kwargs"]
        )
        self.model.max_seq_length = config["max_seq_length"]
