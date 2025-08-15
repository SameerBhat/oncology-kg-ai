"""
GTE (General Text Embedding) Multilingual Base embedding model implementation.

GTE-multilingual-base is a high-performance multilingual embedding model with the following features:
- High Performance: Achieves state-of-the-art results in multilingual retrieval tasks
- Multilingual: Supports over 70 languages
- Long Context: Supports text lengths up to 8192 tokens
- Efficient: 305M parameters with 768-dimensional embeddings
- Fast: 10x faster inference than decoder-only models

Model Details:
- Model Size: 305M parameters
- Embedding Dimension: 768
- Max Input Tokens: 8192
- Architecture: Encoder-only transformer

Paper: mGTE: Generalized Long-Context Text Representation and Reranking Models for Multilingual Text Retrieval
"""
from typing import Dict, Any

from sentence_transformers import SentenceTransformer

from .base import EmbeddingModel


class GTEMultilingualBaseEmbedding(EmbeddingModel):
    """GTE Multilingual Base embedding model implementation using sentence-transformers."""
    
    # Model configuration - all in one place!
    MODEL_ID = "gte"
    MODEL_NAME = "Alibaba-NLP/gte-multilingual-base"
    MAX_SEQ_LENGTH = 8192
    EMBEDDING_DIMENSION = 768
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model-specific configuration for GTE multilingual base."""
        return {
            "model_name": self.MODEL_NAME,
            "device": self.device,
            "trust_remote_code": True,  # Required for this model
            "max_seq_length": self.MAX_SEQ_LENGTH,
            "embedding_dimension": self.EMBEDDING_DIMENSION,
            # Model-specific optimizations
            "model_kwargs": {
                "device_map": "auto",
                # Optional: Can enable xformers for acceleration if available
                # "attn_implementation": "eager"  # Use default attention for stability
            }
        }
    
    def load_model(self) -> None:
        """Load the GTE multilingual base model using sentence-transformers."""
        config = self.get_model_config()
        
        # Load the model with sentence-transformers for consistency with other models
        self.model = SentenceTransformer(
            config["model_name"],
            device=config["device"],
            trust_remote_code=config["trust_remote_code"],
            model_kwargs=config["model_kwargs"]
        )
        
        # Ensure max sequence length is properly set
        self.model.max_seq_length = config["max_seq_length"]
        
        # Verify the model loaded correctly
        print(f"GTE multilingual base model loaded successfully")
        print(f"Model device: {self.model.device}")
        print(f"Max sequence length: {self.model.max_seq_length}")
        
        # Optional: Print model info for debugging
        if hasattr(self.model, '_modules'):
            for name, module in self.model._modules.items():
                if hasattr(module, 'max_seq_length'):
                    print(f"Module '{name}' max_seq_length: {module.max_seq_length}")
