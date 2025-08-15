#!/usr/bin/env python3
"""
Advanced search utilities with support for different search modes and model configurations.
"""

import json
import logging
import sys
from typing import List, Dict, Any, Optional

from src import (
    MongoDBClient,
    SearchManager,
    EMBEDDING_MODEL,
)
from src.embedding_utils import setup_logging


def print_search_results(results: List[Dict[str, Any]], show_content_length: int = 200) -> None:
    """Print search results in a formatted way."""
    if not results:
        print("No results found.")
        return
    
    print(f"\nFound {len(results)} results:")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result['score']:.4f} | Model: {result.get('model_used', 'unknown')}")
        print(f"   ID: {result['_id']}")
        
        # Display text content
        text = result.get('text', '')
        if text:
            display_text = text[:show_content_length] + "..." if len(text) > show_content_length else text
            print(f"   Text: {display_text}")
        
        # Display rich text content  
        rich_text = result.get('richText', '')
        if rich_text:
            display_rich = rich_text[:100] + "..." if len(rich_text) > 100 else rich_text
            print(f"   Rich Text: {display_rich}")
        
        # Display notes
        notes = result.get('notes', '')
        if notes:
            display_notes = notes[:150] + "..." if len(notes) > 150 else notes
            print(f"   Notes: {display_notes}")
        
        # Display links
        links = result.get('links', [])
        if links:
            print(f"   Links: {links}")
        
        # Display attributes
        attributes = result.get('attributes', {})
        if attributes:
            print(f"   Attributes: {json.dumps(attributes, indent=6)}")
            
        print("-" * 40)


def interactive_search(search_manager: SearchManager) -> None:
    """Run interactive search mode."""
    print(f"\n🔍 Interactive Search Mode")
    print(f"Using model: {search_manager.embedding_model_name}")
    
    # Show model configuration
    config = search_manager.get_model_specific_search_config()
    print(f"Model config: {config['notes'] if 'notes' in config else 'Standard configuration'}")
    print(f"Recommended top_k: {config['recommended_top_k']}, threshold: {config['recommended_threshold']}")
    
    try:
        while True:
            print("\n" + "="*60)
            query = input("🔍 Enter your search query (or 'quit' to exit): ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                print("Please enter a valid query.")
                continue
            
            try:
                # Get search parameters
                top_k_input = input(f"Number of results (default {config['recommended_top_k']}): ").strip()
                top_k = int(top_k_input) if top_k_input else config['recommended_top_k']
                
                threshold_input = input(f"Minimum score threshold (default {config['recommended_threshold']}): ").strip()
                threshold = float(threshold_input) if threshold_input else config['recommended_threshold']
                
                # Perform search
                print(f"\n🔄 Searching for: '{query}'...")
                results = search_manager.cosine_search(query, top_k=top_k, threshold=threshold)
                
                # Display results
                print_search_results(results)
                
            except ValueError:
                print("Please enter valid numbers for top_k and threshold.")
            except Exception as e:
                logging.exception(f"Search failed: {e}")
                print(f"❌ Search failed: {e}")
    
    except KeyboardInterrupt:
        print("\n\n👋 Search interrupted by user.")


def batch_search(search_manager: SearchManager, queries: List[str], top_k: int = 5, threshold: float = 0.0) -> None:
    """Run batch search for multiple queries."""
    print(f"\n📊 Batch Search Mode")
    print(f"Processing {len(queries)} queries...")
    
    results = search_manager.batch_search(queries, top_k=top_k, threshold=threshold)
    
    for query, query_results in results.items():
        print(f"\n🔍 Query: '{query}'")
        print_search_results(query_results)
        print("\n" + "="*80)


def similarity_search(search_manager: SearchManager, node_id: str, top_k: int = 5) -> None:
    """Find nodes similar to a given node."""
    print(f"\n🔗 Similarity Search Mode")
    print(f"Finding nodes similar to: {node_id}")
    
    try:
        results = search_manager.get_similar_nodes(node_id, top_k=top_k)
        print_search_results(results)
    except Exception as e:
        logging.exception(f"Similarity search failed: {e}")
        print(f"❌ Similarity search failed: {e}")


def show_stats(search_manager: SearchManager) -> None:
    """Show database and search statistics."""
    print(f"\n📈 Database Statistics")
    stats = search_manager.get_search_stats()
    
    print(f"Database: {search_manager.client.database_name}")
    print(f"Collection: {search_manager.collection_name}")
    print(f"Embedding Model: {stats['embedding_model']}")
    print(f"Total nodes: {stats['total_nodes']}")
    print(f"Nodes with embeddings: {stats['total_nodes_with_embeddings']}")
    print(f"Nodes without embeddings: {stats['nodes_without_embeddings']}")
    
    if stats['total_nodes_with_embeddings'] == 0:
        print("\n⚠️  No embedded nodes found. Run generate_db_embeddings.py first.")
    else:
        coverage = (stats['total_nodes_with_embeddings'] / stats['total_nodes']) * 100
        print(f"Embedding coverage: {coverage:.1f}%")


def main() -> None:
    """Main function with different search modes."""
    setup_logging()
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Search through embedded documents")
    parser.add_argument("--mode", choices=["interactive", "batch", "similarity", "stats"], 
                       default="interactive", help="Search mode")
    parser.add_argument("--query", help="Single query for quick search")
    parser.add_argument("--queries", nargs="+", help="Multiple queries for batch search")
    parser.add_argument("--node-id", help="Node ID for similarity search")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    parser.add_argument("--threshold", type=float, default=0.0, help="Minimum similarity threshold")
    parser.add_argument("--model", help="Override embedding model from environment")
    
    args = parser.parse_args()
    
    # Determine embedding model
    model_name = args.model or EMBEDDING_MODEL
    print(f"🚀 Starting search with model: {model_name}")
    
    # Initialize search manager
    with MongoDBClient() as db_client:
        search_manager = SearchManager(db_client, embedding_model_name=model_name)
        
        # Check if we have any embedded nodes (except for stats mode)
        if args.mode != "stats":
            stats = search_manager.get_search_stats()
            if stats["total_nodes_with_embeddings"] == 0:
                print("❌ No nodes with embeddings found. Please run generate_db_embeddings.py first.")
                sys.exit(1)
        
        # Execute based on mode
        if args.mode == "stats":
            show_stats(search_manager)
        
        elif args.mode == "interactive":
            if args.query:
                # Quick single query
                print(f"🔍 Quick search: '{args.query}'")
                results = search_manager.cosine_search(args.query, top_k=args.top_k, threshold=args.threshold)
                print_search_results(results)
            else:
                interactive_search(search_manager)
        
        elif args.mode == "batch":
            queries = args.queries or []
            if not queries:
                print("❌ No queries provided for batch search. Use --queries option.")
                sys.exit(1)
            batch_search(search_manager, queries, top_k=args.top_k, threshold=args.threshold)
        
        elif args.mode == "similarity":
            if not args.node_id:
                print("❌ No node ID provided for similarity search. Use --node-id option.")
                sys.exit(1)
            similarity_search(search_manager, args.node_id, top_k=args.top_k)
        
        print(f"\n✅ Search completed using {model_name}")


if __name__ == "__main__":
    main()
