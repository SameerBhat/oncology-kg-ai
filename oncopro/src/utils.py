import os
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import torch
load_dotenv()

MAX_TOKENS = 8192
AVG_WORDS_PER_TOKEN = 0.75
MAX_WORDS = int(MAX_TOKENS / AVG_WORDS_PER_TOKEN)

MONGO_URI = os.getenv("DATABASE_URI", "mongodb://localhost:27017")
DATABASE_NAME = "oncopro"

# Configuration for embedding model selection
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "jina")  # Default to jina

# Configuration for embedding model selection
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "jina")  # Default to jina

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
    
    def __init__(self, max_retries: int = 3, delay: int = 5):
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
        """
        chunks = split_text_into_chunks(text)
        embeddings = self.encode_chunks(chunks, **kwargs)
        avg_embedding = embeddings.mean(dim=0).cpu().tolist()
        return avg_embedding

class JinaEmbedding(EmbeddingModel):
    """Jina AI embedding model implementation."""
    
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "model_name": "jinaai/jina-embeddings-v4",
            "trust_remote_code": True,
            "device": self.device,
            "model_kwargs": {
                "attn_implementation": "eager",
                "default_task": "retrieval",
            },
            "max_seq_length": 8192
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

class QwenEmbedding(EmbeddingModel):
    """Qwen3 embedding model implementation."""
    
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "model_name": "Qwen/Qwen3-Embedding-4B",
            "trust_remote_code": True,
            "model_kwargs": {"device_map": "auto"},
            "tokenizer_kwargs": {"padding_side": "left"},
            "max_seq_length": 32768
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
        chunks = split_text_into_chunks(text)
        embeddings = self.encode_chunks(chunks, prompt_name=prompt_name, **kwargs)
        avg_embedding = embeddings.mean(dim=0).cpu().tolist()
        return avg_embedding

class OpenAIEmbedding(EmbeddingModel):
    """Example OpenAI embedding model implementation (placeholder)."""
    
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "model_name": "text-embedding-3-large",  # Example
            "max_seq_length": 8192
        }
    
    def load_model(self) -> None:
        # This is a placeholder - you'd implement OpenAI API calls here
        raise NotImplementedError("OpenAI embedding implementation needed")

class EmbeddingModelFactory:
    """Factory class for creating embedding models."""
    
    _models = {
        "jina": JinaEmbedding,
        "qwen": QwenEmbedding,
        "qwen3": QwenEmbedding,  # Alias
        "openai": OpenAIEmbedding,
    }
    
    @classmethod
    def create_model(cls, model_name: str, **kwargs) -> EmbeddingModel:
        """Create an embedding model by name."""
        if model_name not in cls._models:
            available_models = ", ".join(cls._models.keys())
            raise ValueError(f"Unknown model '{model_name}'. Available models: {available_models}")
        
        return cls._models[model_name](**kwargs)
    
    @classmethod
    def register_model(cls, name: str, model_class: type) -> None:
        """Register a new embedding model class."""
        if not issubclass(model_class, EmbeddingModel):
            raise ValueError(f"Model class must inherit from EmbeddingModel")
        cls._models[name] = model_class
    
    @classmethod
    def list_available_models(cls) -> List[str]:
        """List all available model names."""
        return list(cls._models.keys())

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
    
    Args:
        text: Text to embed
        model_name: Name of the model to use. If None, uses default.
        **kwargs: Additional arguments passed to the model's embed_text method
    
    Returns:
        List of floats representing the embedding vector
    """
    model = get_embedding_model(model_name)
    return model.embed_text(text, **kwargs)

# Backward compatibility functions
def embed_text_using_jina_model(text: str) -> List[float]:
    """Legacy function for backward compatibility."""
    return embed_text(text, model_name="jina")

def embed_text_using_qwen3_model(text: str, *, prompt_name: Optional[str] = None) -> List[float]:
    """Legacy function for backward compatibility."""
    return embed_text(text, model_name="qwen", prompt_name=prompt_name)

def split_text_into_chunks(text, max_words=MAX_WORDS):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = ' '.join(words[i:i + max_words])
        chunks.append(chunk)
    return chunks

# Example usage and documentation:
"""
Usage Examples:

1. Using environment variable (recommended):
   Set EMBEDDING_MODEL=jina (or qwen, openai) in your .env file
   
   # Simple usage
   embedding = embed_text("Your text here")
   
   # Get the model instance
   model = get_embedding_model()

2. Specifying model explicitly:
   embedding = embed_text("Your text here", model_name="jina")
   embedding = embed_text("Your text here", model_name="qwen", prompt_name="query")

3. Adding a new custom model:
   class MyCustomEmbedding(EmbeddingModel):
       def get_model_config(self):
           return {"model_name": "my-model", "max_seq_length": 512}
       
       def load_model(self):
           self.model = SentenceTransformer(self.get_model_config()["model_name"])
   
   # Register the new model
   EmbeddingModelFactory.register_model("custom", MyCustomEmbedding)
   
   # Use it
   embedding = embed_text("Your text here", model_name="custom")

4. List available models:
   available_models = EmbeddingModelFactory.list_available_models()
   print(f"Available models: {available_models}")

5. Force reload a model:
   model = get_embedding_model("jina", force_reload=True)

Supported Models:
- jina: Jina AI embeddings v4 (8192 context length)
- qwen/qwen3: Qwen3 embedding models (32k context length)
- openai: OpenAI embeddings (placeholder - needs implementation)
"""



