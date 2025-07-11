"""
Qwen3 embedding model implementation.
"""
from typing import Dict, Any, List, Optional

from sentence_transformers import SentenceTransformer

from .base import EmbeddingModel
from ..config import QWEN_MODEL_NAME, QWEN_MAX_SEQ_LENGTH


class QwenEmbedding(EmbeddingModel):
    """Qwen3 embedding model implementation."""
    
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "model_name": QWEN_MODEL_NAME,
            "trust_remote_code": True,
            "model_kwargs": {"device_map": "auto"},
            "tokenizer_kwargs": {"padding_side": "left"},
            "max_seq_length": QWEN_MAX_SEQ_LENGTH
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
        # Import here to avoid circular imports
        from ..config import MAX_WORDS
        
        def split_text_into_chunks(text: str, max_words: int = MAX_WORDS) -> List[str]:
            """Split text into chunks of specified maximum word count."""
            words = text.split()
            chunks = []
            for i in range(0, len(words), max_words):
                chunk = ' '.join(words[i:i + max_words])
                chunks.append(chunk)
            return chunks
        
        chunks = split_text_into_chunks(text)
        embeddings = self.encode_chunks(chunks, prompt_name=prompt_name, **kwargs)
        avg_embedding = embeddings.mean(dim=0).cpu().tolist()
        return avg_embedding
