#!/usr/bin/env python3
"""
Test script for the modular embedding system.
"""

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    
    try:
        from src import embed_text, EmbeddingModelFactory, get_embedding_model
        print("✓ Main functions imported successfully")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    try:
        from src.embeddings import EmbeddingModel, JinaEmbedding, QwenEmbedding
        print("✓ Embedding classes imported successfully")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    try:
        from src.config import MAX_WORDS, EMBEDDING_MODEL
        print("✓ Configuration imported successfully")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    return True

def test_factory():
    """Test the embedding factory."""
    print("\nTesting EmbeddingModelFactory...")
    
    try:
        from src import EmbeddingModelFactory
        models = EmbeddingModelFactory.list_available_models()
        print(f"✓ Available models: {models}")
        
        # Test creating a model (without loading)
        jina_model = EmbeddingModelFactory.create_model("jina")
        print(f"✓ Created Jina model: {jina_model.__class__.__name__}")
        
        return True
    except Exception as e:
        print(f"✗ Factory test error: {e}")
        return False

def test_text_processing():
    """Test text processing functions."""
    print("\nTesting text processing...")
    
    try:
        from src import split_text_into_chunks
        
        test_text = "This is a test sentence. " * 100  # Create long text
        chunks = split_text_into_chunks(test_text)
        print(f"✓ Split text into {len(chunks)} chunks")
        
        return True
    except Exception as e:
        print(f"✗ Text processing error: {e}")
        return False

def main():
    """Run all tests."""
    print("=== Testing Modular Embedding System ===\n")
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test factory
    if not test_factory():
        all_passed = False
    
    # Test text processing
    if not test_text_processing():
        all_passed = False
    
    print(f"\n=== Test Results ===")
    if all_passed:
        print("✓ All tests passed! Modular structure is working correctly.")
    else:
        print("✗ Some tests failed. Please check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    main()
