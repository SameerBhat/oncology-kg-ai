"""
BGE-M3 embedding model implementation.

BGE-M3 is a versatile embedding model with Multi-Functionality, Multi-Linguality, and Multi-Granularity:
- Multi-Functionality: Supports dense, sparse (lexical), and multi-vector (ColBERT) retrieval
- Multi-Linguality: Supports 100+ languages
- Multi-Granularity: Handles inputs from short sentences to long documents (up to 8192 tokens)

This implementation uses sentence-transformers for consistency with other models in the pipeline.
For advanced features (sparse embeddings, ColBERT), consider using FlagEmbedding.BGEM3FlagModel directly.

Key features:
- No instruction prompts needed (unlike NV-Embed-v2)
- Built-in multilingual support
- Long document support (8192 tokens)
- High performance on MTEB benchmarks

Usage for fair comparison: Use inherited encode_chunks() and embed_text() methods
Usage for optimal performance: Use encode_chunks_optimized() and embed_text_optimized() methods
"""
from typing import Dict, Any, List, Optional
import torch

from sentence_transformers import SentenceTransformer

from .base import EmbeddingModel


class BGEM3Embedding(EmbeddingModel):
    """BGE-M3 embedding model implementation using sentence-transformers."""
    
    # Model configuration - all in one place!
    MODEL_ID = "bgem3"
    MODEL_NAME = "BAAI/bge-m3"
    MAX_SEQ_LENGTH = 8192
    
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "model_name": self.MODEL_NAME,
            "trust_remote_code": True,
            "model_kwargs": {"device_map": "auto"},
            "max_seq_length": self.MAX_SEQ_LENGTH
        }
    
    def load_model(self) -> None:
        config = self.get_model_config()
        self.model = SentenceTransformer(
            config["model_name"],
            trust_remote_code=config["trust_remote_code"],
            model_kwargs=config["model_kwargs"]
        )
        self.model.max_seq_length = config["max_seq_length"]
    
    def encode_chunks_optimized(self, chunks: List[str], **kwargs) -> torch.Tensor:
        """
        Encode text chunks with BGE-M3 specific optimizations.
        Use this method when you want optimal performance from BGE-M3.
        For fair comparison with other models, use the inherited encode_chunks() method.
        
        Note: BGE-M3 supports multiple retrieval modes (dense, sparse, multi-vector),
        but this implementation focuses on dense embeddings for consistency.
        
        For advanced features like sparse embeddings and ColBERT, consider using:
        from FlagEmbedding import BGEM3FlagModel
        model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
        output = model.encode(texts, return_dense=True, return_sparse=True, return_colbert_vecs=True)
        """
        if self.model is None:
            self.load_with_retry()
        
        # BGE-M3 doesn't require instructions like NV-Embed-v2
        # It can handle queries and passages without special prefixes
        
        # Set normalization for optimal performance
        kwargs['normalize_embeddings'] = True
        
        return self.model.encode(
            chunks,
            convert_to_tensor=True,
            **kwargs
        )
    
    def embed_text_optimized(self, text: str, **kwargs) -> List[float]:
        """
        Embed text using BGE-M3 optimizations (normalization).
        Use this method when you want optimal performance from BGE-M3.
        For fair comparison with other models, use the inherited embed_text() method.
        """
        # Use a simple chunking approach
        max_words = 6000  # Conservative default for 8192 token limit
        words = text.split()
        chunks = []
        for i in range(0, len(words), max_words):
            chunk = ' '.join(words[i:i + max_words])
            chunks.append(chunk)
        
        embeddings = self.encode_chunks_optimized(chunks, **kwargs)
        avg_embedding = embeddings.mean(dim=0).cpu().tolist()
        return avg_embedding
