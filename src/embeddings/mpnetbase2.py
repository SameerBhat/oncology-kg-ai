"""
Paraphrase Multilingual MPNet Base v2 embedding model implementation.
This model maps sentences & paragraphs to a 768 dimensional dense vector space
and supports 50+ languages.
"""
from typing import Dict, Any

from sentence_transformers import SentenceTransformer

from .base import EmbeddingModel


class MPNetBase2Embedding(EmbeddingModel):
    """Paraphrase Multilingual MPNet Base v2 embedding model implementation."""
    
    # Model configuration - all in one place!
    MODEL_ID = "mpnetbase2"
    MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    MAX_SEQ_LENGTH = 128  # As specified in the model architecture
    EMBEDDING_DIMENSION = 768  # Output dimension
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model-specific configuration for MPNet Base v2."""
        return {
            "model_name": self.MODEL_NAME,
            "device": self.device,
            "max_seq_length": self.MAX_SEQ_LENGTH,
            "embedding_dimension": self.EMBEDDING_DIMENSION,
            # This model doesn't require trust_remote_code as it's a standard sentence-transformers model
            "trust_remote_code": False,
        }
    
    def load_model(self) -> None:
        """Load the MPNet Base v2 model using sentence-transformers."""
        config = self.get_model_config()
        
        # Load the model with sentence-transformers
        self.model = SentenceTransformer(
            config["model_name"],
            device=config["device"]
        )
        
        # Ensure max sequence length is properly set
        self.model.max_seq_length = config["max_seq_length"]
        
        # Verify model configuration matches expected values
        if hasattr(self.model, '_modules'):
            # Get the transformer module to check actual max_seq_length
            transformer_module = None
            for module in self.model._modules.values():
                if hasattr(module, 'max_seq_length'):
                    transformer_module = module
                    break
            
            if transformer_module and transformer_module.max_seq_length != self.MAX_SEQ_LENGTH:
                print(f"Warning: Model's internal max_seq_length ({transformer_module.max_seq_length}) "
                      f"differs from configured value ({self.MAX_SEQ_LENGTH})")
