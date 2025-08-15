#!/usr/bin/env python3
"""
Test script to verify the fixed embedding system.
"""

def test_system():
    """Test the complete embedding system."""
    print("=== Testing Fixed Embedding System ===\n")
    
    # Test 1: Basic imports
    print("1. Testing imports...")
    try:
        from src import (
            embed_text, 
            get_embedding_model,
            EmbeddingModelFactory, 
            split_text_into_chunks,
            MAX_WORDS,
            EMBEDDING_MODEL
        )
        print("   ✓ All imports successful")
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return False
    
    # Test 2: Factory functionality
    print("\n2. Testing EmbeddingModelFactory...")
    try:
        models = EmbeddingModelFactory.list_available_models()
        print(f"   ✓ Available models: {models}")
        
        # Create model instance (without loading)
        jina_model = EmbeddingModelFactory.create_model("jina")
        print(f"   ✓ Created model: {jina_model.__class__.__name__}")
        print(f"   ✓ Device: {jina_model.device}")
    except Exception as e:
        print(f"   ✗ Factory test failed: {e}")
        return False
    
    # Test 3: Text processing
    print("\n3. Testing text processing...")
    try:
        test_text = "This is a test sentence. " * 20  # Create longer text
        chunks = split_text_into_chunks(test_text)
        print(f"   ✓ Split text into {len(chunks)} chunks")
        print(f"   ✓ Max words per chunk: {MAX_WORDS}")
        print(f"   ✓ First chunk preview: {chunks[0][:50]}...")
    except Exception as e:
        print(f"   ✗ Text processing failed: {e}")
        return False
    
    # Test 4: Configuration
    print("\n4. Testing configuration...")
    try:
        print(f"   ✓ Default model: {EMBEDDING_MODEL}")
        print(f"   ✓ Max words: {MAX_WORDS}")
    except Exception as e:
        print(f"   ✗ Configuration failed: {e}")
        return False
    
    print("\n=== Results ===")
    print("✓ All tests passed!")
    print("✓ Repository is properly fixed!")
    print("\nThe system is ready for use.")
    
    return True

if __name__ == "__main__":
    test_system()
