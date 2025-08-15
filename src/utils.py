"""
Utility functions for text processing and embedding operations.
"""
from typing import List, Optional

from .config import MAX_WORDS, EMBEDDING_MODEL
from .embeddings import EmbeddingModelFactory, EmbeddingModel


def split_text_into_chunks(text: str, max_words: int = MAX_WORDS) -> List[str]:
    """
    Split text into chunks of specified maximum word count.
    
    Args:
        text: Input text to split
        max_words: Maximum number of words per chunk
        
    Returns:
        List of text chunks
    """
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = ' '.join(words[i:i + max_words])
        chunks.append(chunk)
    return chunks


# Global embedding model instance
_embedding_model: Optional[EmbeddingModel] = None


def get_embedding_model(model_name: Optional[str] = None, force_reload: bool = False) -> EmbeddingModel:
    """
    Get the global embedding model instance.
    
    Args:
        model_name: Name of the model to use. If None, uses EMBEDDING_MODEL env var.
        force_reload: If True, force reload the model even if already loaded.
    
    Returns:
        EmbeddingModel instance
    """
    global _embedding_model
    
    if model_name is None:
        model_name = EMBEDDING_MODEL
    
    if _embedding_model is None or force_reload:
        _embedding_model = EmbeddingModelFactory.create_model(model_name)
        _embedding_model.load_with_retry()
    
    return _embedding_model


def embed_text(text: str, model_name: Optional[str] = None, **kwargs) -> List[float]:
    """
    Embed text using the specified or default embedding model.
    
    This function uses the proper chunking configuration and provides
    a centralized way to embed text with any supported model.
    
    Args:
        text: Text to embed
        model_name: Name of the model to use. If None, uses default.
        **kwargs: Additional arguments passed to the model's embed_text method
    
    Returns:
        List of floats representing the embedding vector
    """
    # For the high-level embed_text function, we want to use proper chunking
    # so we override the model's basic embed_text method
    model = get_embedding_model(model_name)
    
    # Use the proper chunking from utils
    chunks = split_text_into_chunks(text)
    embeddings = model.encode_chunks(chunks, **kwargs)
    avg_embedding = embeddings.mean(dim=0).cpu().tolist()
    return avg_embedding


# Backward compatibility functions
def embed_text_using_jina_model(text: str) -> List[float]:
    """Legacy function for backward compatibility."""
    return embed_text(text, model_name="jina")


def embed_text_using_qwen3_model(text: str, *, prompt_name: Optional[str] = None) -> List[float]:
    """Legacy function for backward compatibility."""
    return embed_text(text, model_name="qwen", prompt_name=prompt_name)
