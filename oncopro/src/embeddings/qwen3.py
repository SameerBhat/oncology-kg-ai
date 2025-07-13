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
    
    def embed_text(self, text: str, prompt_name: Optional[str] = None, **kwargs) -> List[float]:
        """
        Embed text with optional prompt_name for Qwen3.
        Use prompt_name='query' when embedding queries (recommended by Qwen3 docs).
        """
        # Use a simple chunking approach directly here to avoid circular imports
        max_words = 6000  # Conservative default
        words = text.split()
        chunks = []
        for i in range(0, len(words), max_words):
            chunk = ' '.join(words[i:i + max_words])
            chunks.append(chunk)
        
        embeddings = self.encode_chunks(chunks, prompt_name=prompt_name, **kwargs)
        avg_embedding = embeddings.mean(dim=0).cpu().tolist()
        return avg_embedding
