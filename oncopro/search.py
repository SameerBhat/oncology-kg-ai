#!/usr/bin/env python3
"""
Search functionality for querying embeddings using cosine similarity.
This script allows searching through embedded nodes using various embedding models.
"""

import logging
import sys
from typing import List, Dict, Any, Optional

from src import (
    embed_text,
    MongoDBClient,
    EMBEDDING_MODEL,
)
from src.embedding_utils import setup_logging
from src.search import SearchManager


def main() -> None:
    """Main function for interactive search."""
    # Set up logging
    setup_logging()
    
    # Log which model we're using
    logging.info(f"Using embedding model: {EMBEDDING_MODEL}")
    
    # Initialize search manager
    with MongoDBClient() as db_client:
        search_manager = SearchManager(db_client)
        
        # Check if we have any embedded nodes
        stats = search_manager.get_search_stats()
        
        if stats["total_nodes_with_embeddings"] == 0:
            logging.error("No nodes with embeddings found. Please run generate_db_embeddings.py first.")
            sys.exit(1)
        
        logging.info(f"Found {stats['total_nodes_with_embeddings']} nodes with embeddings")
        
        # Interactive search loop
        try:
            while True:
                query = input("\nEnter your search query (or 'quit' to exit): ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not query:
                    print("Please enter a valid query.")
                    continue
                
                try:
                    # Get top_k from user (default to 5)
                    top_k_input = input("Number of results (default 5): ").strip()
                    top_k = int(top_k_input) if top_k_input else 5
                    
                    # Perform search
                    results = search_manager.cosine_search(query, top_k=top_k)
                    
                    # Display results
                    if not results:
                        print("No results found.")
                    else:
                        print(f"\nTop {len(results)} results:")
                        print("-" * 60)
                        
                        for i, result in enumerate(results, 1):
                            print(f"{i}. Score: {result['score']:.4f}")
                            print(f"   Content: {result['content'][:200]}...")
                            if result.get('metadata'):
                                print(f"   Metadata: {result['metadata']}")
                            print()
                
                except ValueError:
                    print("Please enter a valid number for top_k.")
                except Exception as e:
                    logging.exception(f"Search failed: {e}")
                    print(f"Search failed: {e}")
        
        except KeyboardInterrupt:
            print("\nSearch interrupted by user.")
        
        logging.info("Search session ended.")


if __name__ == "__main__":
    main()