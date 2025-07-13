#!/usr/bin/env python3
"""
Example: Adding a new embedding model with centralized configuration.
This demonstrates how easy it is to add a new model.
"""
from typing import Dict, Any, List
from src.embeddings.base import EmbeddingModel
from src.embeddings.factory import EmbeddingModelFactory


class BGEEmbedding(EmbeddingModel):
    """BGE embedding model - new model added with centralized config."""
    
    # All configuration in one place - that's it!
    MODEL_ID = "bge"
    MODEL_NAME = "BAAI/bge-large-en-v1.5"
    MAX_SEQ_LENGTH = 512
    
    def get_model_config(self) -> Dict[str, Any]:
        return {
            "model_name": self.MODEL_NAME,
            "trust_remote_code": True,
            "device": self.device,
            "max_seq_length": self.MAX_SEQ_LENGTH
        }
    
    def load_model(self) -> None:
        # Would implement actual loading here
        print(f"Loading {self.MODEL_NAME} model...")
        # self.model = SentenceTransformer(...)
        self.model = "mock_model"  # Mock for demo
    
    def embed_text(self, text: str, **kwargs) -> List[float]:
        # Would implement actual embedding here
        return [0.1, 0.2, 0.3]  # Mock embedding


def demo_new_model():
    """Demo adding a new model."""
    print("🚀 Adding a new embedding model with centralized configuration!")
    
    # Step 1: Register the new model (this could be automatic with module discovery)
    EmbeddingModelFactory.register_model(BGEEmbedding)
    
    # Step 2: That's it! The model is now available
    models = EmbeddingModelFactory.list_available_models()
    print(f"Available models: {models}")
    
    # Step 3: Get info about our new model
    info = EmbeddingModelFactory.get_model_info("bge")
    print(f"\nNew BGE model info:")
    print(f"  ID: {info['id']}")
    print(f"  Name: {info['name']}")
    print(f"  Max Seq Length: {info['max_seq_length']}")
    
    # Step 4: Create and use the model
    model = EmbeddingModelFactory.create_model("bge")
    print(f"\nCreated model: {model.__class__.__name__}")
    print(f"Model ID: {model.MODEL_ID}")
    
    print("\n✅ New model added successfully!")
    print("💡 To add a new model, you only need to:")
    print("   1. Create a class inheriting from EmbeddingModel")
    print("   2. Define MODEL_ID, MODEL_NAME, and MAX_SEQ_LENGTH")
    print("   3. Implement get_model_config() and load_model()")
    print("   4. Register it with the factory (or use auto-discovery)")
    print("\n🎯 All configuration is centralized in the model class itself!")


if __name__ == "__main__":
    demo_new_model()
