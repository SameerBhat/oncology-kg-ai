"""
Jina AI embedding model implementation.
"""
from typing import Dict, Any

from sentence_transformers import SentenceTransformer

from .base import EmbeddingModel
from ..config import JINA4_MODEL_NAME, JINA4_MAX_SEQ_LENGTH


class Jina4Embedding(EmbeddingModel):
    """Jina AI embedding model implementation."""
    
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "model_name": JINA4_MODEL_NAME,
            "trust_remote_code": True,
            "device": self.device,
            "model_kwargs": {
                "attn_implementation": "eager",
                "default_task": "retrieval",
            },
            "max_seq_length": JINA4_MAX_SEQ_LENGTH
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
