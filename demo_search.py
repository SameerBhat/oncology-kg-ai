#!/usr/bin/env python3
"""
Example usage of the search functionality with different embedding models.
This script demonstrates how to switch between models and perform searches.
"""

import os
import logging
from src import MongoDBClient, SearchManager, EMBEDDING_MODEL
from src.embedding_utils import setup_logging


def demo_search_with_current_model():
    """Demonstrate search with the currently configured model."""
    print(f"🔍 Demo: Search with {EMBEDDING_MODEL}")
    
    with MongoDBClient() as db_client:
        search_manager = SearchManager(db_client)
        
        # Show statistics
        stats = search_manager.get_search_stats()
        print(f"Database: {stats['embedding_model']}")
        print(f"Nodes with embeddings: {stats['total_nodes_with_embeddings']}")
        
        if stats['total_nodes_with_embeddings'] == 0:
            print("⚠️  No embedded nodes found. Run generate_db_embeddings.py first.")
            return
        
        # Show model configuration
        config = search_manager.get_model_specific_search_config()
        print(f"Model notes: {config.get('notes', 'No specific notes')}")
        
        # Example searches
        example_queries = [
            "What are the main symptoms?",
            "Treatment options and therapy",
            "Side effects and risks"
        ]
        
        print(f"\n📝 Example searches:")
        for query in example_queries:
            print(f"\n🔍 Query: '{query}'")
            try:
                results = search_manager.cosine_search(
                    query, 
                    top_k=3, 
                    threshold=config['recommended_threshold']
                )
                
                if results:
                    for i, result in enumerate(results, 1):
                        print(f"  {i}. Score: {result['score']:.3f}")
                        
                        # Show the first available content field
                        content = ""
                        if result.get('text'):
                            content = result['text']
                        elif result.get('richText'):
                            content = result['richText']
                        elif result.get('notes'):
                            content = result['notes']
                        
                        if content:
                            display_content = content[:100] + "..." if len(content) > 100 else content
                            print(f"     Content: {display_content}")
                        else:
                            print(f"     Content: [No text content]")
                else:
                    print("  No results found.")
                    
            except Exception as e:
                print(f"  ❌ Search failed: {e}")


def demo_model_switching():
    """Demonstrate how to search with different models."""
    from src.embeddings import EmbeddingModelFactory
    
    print(f"\n🔄 Demo: Model Switching")
    
    # Get available models
    available_models = EmbeddingModelFactory.list_available_models()
    print(f"Available models: {', '.join(available_models)}")
    
    # Try searching with different models (if they have databases)
    test_query = "medical treatment"
    
    for model_name in available_models[:3]:  # Test first 3 models
        print(f"\n🧪 Testing with {model_name}:")
        
        try:
            # Create a search manager with specific model
            with MongoDBClient(database_name=model_name) as db_client:
                search_manager = SearchManager(
                    db_client, 
                    embedding_model_name=model_name
                )
                
                stats = search_manager.get_search_stats()
                if stats['total_nodes_with_embeddings'] > 0:
                    results = search_manager.cosine_search(test_query, top_k=2)
                    print(f"  Found {len(results)} results")
                    if results:
                        print(f"  Best match score: {results[0]['score']:.3f}")
                else:
                    print(f"  No embeddings found for {model_name}")
                    
        except Exception as e:
            print(f"  ❌ Failed to test {model_name}: {e}")


def demo_advanced_search_features():
    """Demonstrate advanced search features."""
    print(f"\n🎯 Demo: Advanced Search Features")
    
    with MongoDBClient() as db_client:
        search_manager = SearchManager(db_client)
        
        stats = search_manager.get_search_stats()
        if stats['total_nodes_with_embeddings'] == 0:
            print("⚠️  No embedded nodes found. Skipping advanced demo.")
            return
        
        # Batch search
        queries = ["symptoms", "treatment", "diagnosis"]
        print(f"\n📊 Batch search with queries: {queries}")
        
        try:
            batch_results = search_manager.batch_search(queries, top_k=2)
            for query, results in batch_results.items():
                print(f"  '{query}': {len(results)} results")
        except Exception as e:
            print(f"  ❌ Batch search failed: {e}")
        
        # Similarity search (if we have nodes)
        try:
            # Get a random node ID to test similarity
            from bson import ObjectId
            sample_node = search_manager.collection.find_one(
                {"embedding": {"$exists": True}}, 
                {"_id": 1}
            )
            
            if sample_node:
                node_id = str(sample_node["_id"])
                print(f"\n🔗 Finding nodes similar to: {node_id[:10]}...")
                
                similar_nodes = search_manager.get_similar_nodes(node_id, top_k=2)
                print(f"  Found {len(similar_nodes)} similar nodes")
                if similar_nodes:
                    print(f"  Most similar score: {similar_nodes[0]['score']:.3f}")
            
        except Exception as e:
            print(f"  ❌ Similarity search failed: {e}")


def main():
    """Run all demonstrations."""
    setup_logging()
    
    print("🚀 OnCoPro Search System Demo")
    print("=" * 50)
    
    try:
        demo_search_with_current_model()
        demo_model_switching()
        demo_advanced_search_features()
        
        print(f"\n✅ Demo completed!")
        print(f"\n💡 Tips:")
        print(f"   - Use search.py for interactive search")
        print(f"   - Use search_advanced.py for more options")
        print(f"   - Change EMBEDDING_MODEL in .env to switch models")
        print(f"   - Each model uses its own database: {EMBEDDING_MODEL}")
        
    except Exception as e:
        logging.exception("Demo failed")
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    main()
