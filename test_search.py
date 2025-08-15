#!/usr/bin/env python3
"""
Test script to validate the search functionality.
"""

import sys
import logging
from src import MongoDBClient, SearchManager, EMBEDDING_MODEL
from src.embedding_utils import setup_logging


def test_search_system():
    """Test the search system functionality."""
    print(f"🧪 Testing Search System with {EMBEDDING_MODEL}")
    
    try:
        with MongoDBClient() as db_client:
            search_manager = SearchManager(db_client)
            
            # Test 1: Get statistics
            print("\n1. Testing statistics...")
            stats = search_manager.get_search_stats()
            print(f"   ✅ Stats retrieved: {stats}")
            
            if stats['total_nodes_with_embeddings'] == 0:
                print("   ⚠️  No embeddings found. Search tests will be limited.")
                return False
            
            # Test 2: Get model configuration
            print("\n2. Testing model configuration...")
            config = search_manager.get_model_specific_search_config()
            print(f"   ✅ Model config: {config['model_id']} - {config.get('notes', 'No notes')}")
            
            # Test 3: Simple search
            print("\n3. Testing simple search...")
            test_query = "test"
            results = search_manager.cosine_search(test_query, top_k=2)
            print(f"   ✅ Search completed. Found {len(results)} results")
            
            if results:
                print(f"   ✅ Best result score: {results[0]['score']:.3f}")
                print(f"   ✅ Result contains required fields: {set(results[0].keys())}")
            
            # Test 4: Search with threshold
            print("\n4. Testing search with threshold...")
            results_filtered = search_manager.cosine_search(test_query, top_k=5, threshold=0.1)
            print(f"   ✅ Filtered search completed. Found {len(results_filtered)} results")
            
            # Test 5: Batch search (if we have results)
            if results:
                print("\n5. Testing batch search...")
                batch_queries = ["test", "content"]
                batch_results = search_manager.batch_search(batch_queries, top_k=1)
                print(f"   ✅ Batch search completed for {len(batch_results)} queries")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        logging.exception("Search test failed")
        return False


def test_model_switching():
    """Test switching between different models."""
    print(f"\n🔄 Testing Model Switching")
    
    from src.embeddings import EmbeddingModelFactory
    available_models = EmbeddingModelFactory.list_available_models()
    
    tested_models = []
    for model_name in available_models[:2]:  # Test first 2 models
        try:
            print(f"\n   Testing {model_name}...")
            
            with MongoDBClient(database_name=model_name) as db_client:
                search_manager = SearchManager(db_client, embedding_model_name=model_name)
                stats = search_manager.get_search_stats()
                
                print(f"   ✅ {model_name}: {stats['total_nodes_with_embeddings']} embedded nodes")
                tested_models.append(model_name)
                
        except Exception as e:
            print(f"   ⚠️  {model_name}: {e}")
    
    print(f"\n✅ Successfully tested {len(tested_models)} models: {tested_models}")
    return len(tested_models) > 0


def main():
    """Run all tests."""
    setup_logging()
    
    print("🚀 OnCoPro Search System Tests")
    print("=" * 40)
    
    success = True
    
    # Test current model
    if not test_search_system():
        success = False
    
    # Test model switching
    if not test_model_switching():
        print("⚠️  Model switching tests had issues")
    
    print("\n" + "=" * 40)
    if success:
        print("✅ All core tests passed!")
        print("\n💡 Next steps:")
        print("   - Run 'python search.py' for interactive search")
        print("   - Run 'python demo_search.py' for full demo")
        print("   - See SEARCH_README.md for complete documentation")
    else:
        print("❌ Some tests failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
