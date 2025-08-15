"""
Nomic Embed Text v2 MoE embedding model implementation.
"""
from typing import Dict, Any, List
import torch

from sentence_transformers import SentenceTransformer

from .base import EmbeddingModel


class NomicV2Embedding(EmbeddingModel):
    """Nomic Embed Text v2 MoE embedding model implementation."""
    
    # Model configuration - all in one place!
    MODEL_ID = "nomicv2"
    MODEL_NAME = "nomic-ai/nomic-embed-text-v2-moe"
    MAX_SEQ_LENGTH = 512
    
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "model_name": self.MODEL_NAME,
            "trust_remote_code": True,
            "device": self.device,
            "max_seq_length": self.MAX_SEQ_LENGTH
        }
    
    def load_model(self) -> None:
        config = self.get_model_config()
        self.model = SentenceTransformer(
            config["model_name"],
            trust_remote_code=config["trust_remote_code"],
            device=config["device"]
        )
        self.model.max_seq_length = config["max_seq_length"]

    def encode_chunks(self, chunks: List[str], use_instruction: bool = False, task_name: str = "passage", **kwargs) -> torch.Tensor:
        """
        Encode text chunks with Nomic v2 MoE.
        
        Args:
            chunks: List of text chunks to encode
            use_instruction: Whether to use task-specific instruction prefixes (default: False for fair comparison)
            task_name: Task name for instruction prefix ("passage" for documents, "query" for queries)
            **kwargs: Additional arguments passed to the encoder
        
        Returns:
            Tensor of embeddings
        """
        if self.model is None:
            self.load_with_retry()
        
        # For fair comparison, we don't use instruction prefixes by default
        # This ensures consistent behavior across all models
        if use_instruction:
            # Use SentenceTransformers' built-in prompt handling
            prompt_name = "passage" if task_name == "passage" else "query"
            return self.model.encode(
                chunks,
                convert_to_tensor=True,
                prompt_name=prompt_name,
                **kwargs
            )
        else:
            # Standard encoding without prefixes for fair comparison
            return self.model.encode(
                chunks,
                convert_to_tensor=True,
                **kwargs
            )

    def encode_chunks_optimized(self, chunks: List[str], task_name: str = "passage", **kwargs) -> torch.Tensor:
        """
        Encode text chunks with Nomic v2 MoE specific optimizations.
        Use this method when you want optimal performance from Nomic v2 MoE.
        For fair comparison with other models, use the inherited encode_chunks() method.
        
        Args:
            chunks: List of text chunks to encode
            task_name: Task name for instruction prefix ("passage" for documents, "query" for queries)
            **kwargs: Additional arguments passed to the encoder
        
        Returns:
            Tensor of embeddings
        """
        if self.model is None:
            self.load_with_retry()
        
        # Use model-specific optimizations with proper instruction prefixes
        prompt_name = "passage" if task_name == "passage" else "query"
        return self.model.encode(
            chunks,
            convert_to_tensor=True,
            prompt_name=prompt_name,
            **kwargs
        )
