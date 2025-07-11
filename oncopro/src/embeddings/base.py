"""
Base abstract class for embedding models.
"""
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any

import torch

from ..config import DEFAULT_MAX_RETRIES, DEFAULT_RETRY_DELAY


def get_device():
    """Get the best available device for model inference."""
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"


class EmbeddingModel(ABC):
    """Abstract base class for embedding models."""
    
    def __init__(self, max_retries: int = DEFAULT_MAX_RETRIES, delay: int = DEFAULT_RETRY_DELAY):
        self.max_retries = max_retries
        self.delay = delay
        self.model = None
        self.device = get_device()
        print(f"Using device: {self.device}")
    
    @abstractmethod
    def load_model(self) -> None:
        """Load the embedding model."""
        pass
    
    @abstractmethod
    def get_model_config(self) -> Dict[str, Any]:
        """Get model-specific configuration."""
        pass
    
    def load_with_retry(self) -> None:
        """Load model with retry logic for handling transient errors."""
        for attempt in range(self.max_retries):
            try:
                print(f"Loading {self.__class__.__name__}... (attempt {attempt + 1}/{self.max_retries})")
                self.load_model()
                print("Model loaded successfully!")
                return
            except Exception as e:
                if self._is_transient_error(e):
                    if attempt < self.max_retries - 1:
                        print(f"Transient error hit. Waiting {self.delay} seconds before retry...")
                        time.sleep(self.delay)
                        self.delay *= 2
                    else:
                        print("Max retries reached.")
                        raise
                else:
                    raise
    
    def _is_transient_error(self, error: Exception) -> bool:
        """Check if error is transient and retryable."""
        error_str = str(error).lower()
        return any(code in error_str for code in ["429", "502", "503", "rate"])
    
    def encode_chunks(self, chunks: List[str], **kwargs) -> torch.Tensor:
        """Encode text chunks into embeddings."""
        if self.model is None:
            self.load_with_retry()
        
        return self.model.encode(
            chunks,
            convert_to_tensor=True,
            **kwargs
        )
    
    def embed_text(self, text: str, **kwargs) -> List[float]:
        """
        Embed text by chunking and mean pooling.
        Returns a single embedding vector representing the entire text.
        
        This method should be overridden by subclasses that need special handling.
        """
        # Use a simple chunking approach directly here to avoid circular imports
        # This keeps the base class self-contained
        max_words = 6000  # Conservative default
        words = text.split()
        chunks = []
        for i in range(0, len(words), max_words):
            chunk = ' '.join(words[i:i + max_words])
            chunks.append(chunk)
        
        embeddings = self.encode_chunks(chunks, **kwargs)
        avg_embedding = embeddings.mean(dim=0).cpu().tolist()
        return avg_embedding
