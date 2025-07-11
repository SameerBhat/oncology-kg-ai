#!/usr/bin/env python3
"""
Quick verification that the modular system works correctly.
"""

def test_basic_functionality():
    """Test basic functionality without loading heavy models."""
    print("=== Testing Modular Embedding System ===\n")
    
    # Test 1: Import check
    print("1. Testing imports...")
    try:
        from src import (
            embed_text, 
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
        print(f"   ✓ Created model instance: {jina_model.__class__.__name__}")
        print(f"   ✓ Device detected: {jina_model.device}")
    except Exception as e:
        print(f"   ✗ Factory test failed: {e}")
        return False
    
    # Test 3: Text processing
    print("\n3. Testing text processing...")
    try:
        test_text = "This is a test sentence. " * 50  # Create longer text
        chunks = split_text_into_chunks(test_text)
        print(f"   ✓ Split text into {len(chunks)} chunks")
        print(f"   ✓ First chunk: {chunks[0][:50]}...")
        print(f"   ✓ Max words per chunk: {MAX_WORDS}")
    except Exception as e:
        print(f"   ✗ Text processing failed: {e}")
        return False
    
    # Test 4: Configuration
    print("\n4. Testing configuration...")
    try:
        print(f"   ✓ Default embedding model: {EMBEDDING_MODEL}")
        print(f"   ✓ Max words per chunk: {MAX_WORDS}")
    except Exception as e:
        print(f"   ✗ Configuration test failed: {e}")
        return False
    
    print("\n=== Results ===")
    print("✓ All basic tests passed!")
    print("✓ Modular structure is working correctly!")
    print("\nNotes:")
    print("- To test actual embedding, run with a specific model")
    print("- Heavy model loading is skipped in this basic test")
    
    return True

def test_with_model_loading():
    """Test with actual model loading (optional, requires dependencies)."""
    print("\n=== Optional: Testing with Model Loading ===")
    
    try:
        from src import embed_text
        
        test_text = "This is a simple test for the embedding system."
        print(f"Testing with text: '{test_text}'")
        
        # This will actually load the model
        embedding = embed_text(test_text, model_name="jina")
        print(f"✓ Embedding generated successfully!")
        print(f"✓ Embedding dimension: {len(embedding)}")
        print(f"✓ Sample values: {embedding[:3]}")
        
        return True
    except Exception as e:
        print(f"✗ Model loading test failed: {e}")
        print("  This is expected if dependencies are missing")
        return False

if __name__ == "__main__":
    # Run basic tests (always works)
    success = test_basic_functionality()
    
    # Ask user if they want to test model loading
    if success:
        try:
            response = input("\nTest actual model loading? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                test_with_model_loading()
        except KeyboardInterrupt:
            print("\nSkipping model loading test.")
    
    print("\nDone!")
