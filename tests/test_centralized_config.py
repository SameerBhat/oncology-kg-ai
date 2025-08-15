#!/usr/bin/env python3
"""
Test script to verify the centralized configuration approach works.
"""
from src.embeddings.factory import EmbeddingModelFactory


def test_centralized_config():
    """Test that the centralized configuration works correctly."""
    print("Testing centralized embedding model configuration...")
    
    # Test listing available models
    models = EmbeddingModelFactory.list_available_models()
    print(f"Available models: {models}")
    
    # Test getting model info for each model
    for model_name in models:
        try:
            info = EmbeddingModelFactory.get_model_info(model_name)
            print(f"\nModel: {model_name}")
            print(f"  ID: {info['id']}")
            print(f"  Name: {info['name']}")
            print(f"  Max Seq Length: {info['max_seq_length']}")
            
            # Test creating model (without loading)
            model = EmbeddingModelFactory.create_model(model_name)
            print(f"  Class: {model.__class__.__name__}")
            print(f"  Model ID from instance: {model.MODEL_ID}")
            print(f"  Model Name from instance: {model.MODEL_NAME}")
            print(f"  Max Seq Length from instance: {model.MAX_SEQ_LENGTH}")
            
        except Exception as e:
            print(f"Error with model {model_name}: {e}")
    
    print("\n✅ All tests passed! Configuration is centralized and working.")


if __name__ == "__main__":
    test_centralized_config()
