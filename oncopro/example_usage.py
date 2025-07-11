#!/usr/bin/env python3
"""
Example usage of the refactored embedding system.
"""

import os
from src.utils import (
    embed_text,
    get_embedding_model,
    EmbeddingModelFactory,
    EmbeddingModel
)

def main():
    # Example text to embed
    sample_text = """
    Machine learning is a subset of artificial intelligence that focuses on the development 
    of algorithms and statistical models that enable computer systems to improve their 
    performance on a specific task through experience.
    """
    
    print("=== Embedding System Examples ===\n")
    
    # 1. Using default model (from environment variable)
    print("1. Using default model:")
    try:
        embedding = embed_text(sample_text)
        print(f"   Embedding dimension: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 2. Explicitly specify Jina model
    print("\n2. Using Jina model explicitly:")
    try:
        embedding = embed_text(sample_text, model_name="jina")
        print(f"   Embedding dimension: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 3. Using Qwen model with query prompt
    print("\n3. Using Qwen model with query prompt:")
    try:
        # First for document embedding
        doc_embedding = embed_text(sample_text, model_name="qwen")
        print(f"   Document embedding dimension: {len(doc_embedding)}")
        
        # Then for query embedding
        query_text = "What is machine learning?"
        query_embedding = embed_text(query_text, model_name="qwen", prompt_name="query")
        print(f"   Query embedding dimension: {len(query_embedding)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 4. List available models
    print("\n4. Available models:")
    available_models = EmbeddingModelFactory.list_available_models()
    for model in available_models:
        print(f"   - {model}")
    
    # 5. Get model instance directly
    print("\n5. Working with model instance:")
    try:
        model = get_embedding_model("jina")
        print(f"   Model class: {model.__class__.__name__}")
        print(f"   Device: {model.device}")
        
        # Use model instance directly
        chunks = ["This is chunk 1", "This is chunk 2"]
        embeddings = model.encode_chunks(chunks)
        print(f"   Encoded {len(chunks)} chunks, shape: {embeddings.shape}")
    except Exception as e:
        print(f"   Error: {e}")

class CustomEmbedding(EmbeddingModel):
    """Example custom embedding model."""
    
    def get_model_config(self):
        return {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "max_seq_length": 512
        }
    
    def load_model(self):
        from sentence_transformers import SentenceTransformer
        config = self.get_model_config()
        self.model = SentenceTransformer(config["model_name"])
        self.model.max_seq_length = config["max_seq_length"]

def demonstrate_custom_model():
    print("\n=== Custom Model Example ===")
    
    # Register custom model
    EmbeddingModelFactory.register_model("mini", CustomEmbedding)
    
    try:
        # Use custom model
        embedding = embed_text("This is a test with a smaller model.", model_name="mini")
        print(f"Custom model embedding dimension: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
    demonstrate_custom_model()
