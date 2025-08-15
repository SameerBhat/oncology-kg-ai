#!/usr/bin/env python3
"""
Test script for NomicV2Embedding implementation.
"""
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.embeddings.nomicv2 import NomicV2Embedding
from src.embeddings.factory import EmbeddingModelFactory


def test_nomicv2_basic():
    """Test basic functionality of NomicV2Embedding."""
    print("Testing NomicV2Embedding basic functionality...")
    
    # Test factory creation
    print("1. Testing factory creation...")
    model = EmbeddingModelFactory.create_model("nomicv2")
    print(f"✓ Model created: {model.__class__.__name__}")
    print(f"✓ Model ID: {model.MODEL_ID}")
    print(f"✓ Model Name: {model.MODEL_NAME}")
    print(f"✓ Max Seq Length: {model.MAX_SEQ_LENGTH}")
    
    # Test model configuration
    print("\n2. Testing model configuration...")
    config = model.get_model_config()
    print(f"✓ Model config: {config}")
    
    # Test encoding (this will load the model)
    print("\n3. Testing encoding...")
    test_texts = [
        "Hello world, this is a test document.",
        "This is another test document for embedding comparison."
    ]
    
    try:
        # Test standard encoding (for fair comparison)
        embeddings = model.encode_chunks(test_texts)
        print(f"✓ Standard encoding successful, shape: {embeddings.shape}")
        
        # Test optimized encoding (model-specific)
        embeddings_opt = model.encode_chunks_optimized(test_texts, task_name="passage")
        print(f"✓ Optimized encoding successful, shape: {embeddings_opt.shape}")
        
        # Test single text embedding
        single_embedding = model.embed_text("This is a single test text.")
        print(f"✓ Single text embedding successful, length: {len(single_embedding)}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error during encoding: {e}")
        return False
    
    return True


def test_factory_registration():
    """Test that the model is properly registered in the factory."""
    print("\nTesting factory registration...")
    
    factory = EmbeddingModelFactory()
    models = factory._get_models_registry()
    
    if "nomicv2" in models:
        print("✓ NomicV2 model is registered in factory")
        print(f"✓ Available models: {list(models.keys())}")
        return True
    else:
        print("❌ NomicV2 model is NOT registered in factory")
        print(f"Available models: {list(models.keys())}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("NomicV2Embedding Test Suite")
    print("=" * 60)
    
    # Test factory registration first
    factory_ok = test_factory_registration()
    
    if factory_ok:
        # Only run basic tests if factory registration works
        basic_ok = test_nomicv2_basic()
        
        if basic_ok:
            print("\n🎉 All tests completed successfully!")
            print("\nThe NomicV2Embedding implementation is ready for fair comparison testing.")
            print("\nFor fair comparison, use the standard encode_chunks() method.")
            print("For optimal Nomic-specific performance, use encode_chunks_optimized().")
        else:
            print("\n❌ Basic functionality tests failed.")
            sys.exit(1)
    else:
        print("\n❌ Factory registration test failed.")
        sys.exit(1)
