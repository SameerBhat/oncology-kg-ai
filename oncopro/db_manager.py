#!/usr/bin/env python3
"""
Database management utility for viewing embedding statistics and managing the nodes collection.
"""

import argparse
import logging
from typing import Optional

from src import (
    MongoDBClient, 
    NodesManager,
    EMBEDDING_MODEL,
    setup_logging,
    log_embedding_stats
)


def show_stats(nodes_manager: NodesManager) -> None:
    """Show collection statistics."""
    stats = nodes_manager.get_collection_stats()
    log_embedding_stats(stats)


def show_sample_nodes(nodes_manager: NodesManager, limit: int = 5, with_embeddings: bool = True) -> None:
    """Show sample nodes from the collection."""
    collection = nodes_manager.collection
    
    if with_embeddings:
        filter_query = {"embedding": {"$exists": True}}
        title = f"Sample {limit} nodes WITH embeddings:"
    else:
        filter_query = {"embedding": {"$exists": False}}
        title = f"Sample {limit} nodes WITHOUT embeddings:"
    
    print(f"\n{title}")
    print("=" * len(title))
    
    cursor = collection.find(filter_query).limit(limit)
    
    for i, doc in enumerate(cursor, 1):
        node_id = doc.get('_id')
        text = (doc.get('text') or '')[:100] + '...' if len(doc.get('text', '')) > 100 else doc.get('text', '')
        embedding_dim = len(doc.get('embedding', [])) if doc.get('embedding') else 0
        
        print(f"{i}. ID: {node_id}")
        print(f"   Text: {text}")
        if with_embeddings:
            print(f"   Embedding dimension: {embedding_dim}")
        print()


def clear_all_embeddings(nodes_manager: NodesManager, confirm: bool = False) -> None:
    """Clear all embeddings from the collection."""
    if not confirm:
        response = input("⚠️  This will remove ALL embeddings from the collection. Are you sure? (yes/no): ")
        if response.lower() != 'yes':
            print("Operation cancelled.")
            return
    
    collection = nodes_manager.collection
    result = collection.update_many(
        {"embedding": {"$exists": True}},
        {"$unset": {"embedding": ""}}
    )
    
    print(f"✅ Cleared embeddings from {result.modified_count} nodes.")


def main():
    """Main function for database management."""
    parser = argparse.ArgumentParser(description="Database management utility for embeddings")
    parser.add_argument("--stats", action="store_true", help="Show collection statistics")
    parser.add_argument("--sample-with", type=int, metavar="N", help="Show N sample nodes with embeddings")
    parser.add_argument("--sample-without", type=int, metavar="N", help="Show N sample nodes without embeddings")
    parser.add_argument("--clear-embeddings", action="store_true", help="Clear all embeddings from collection")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompts")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    logging.info(f"Using database for embedding model: {EMBEDDING_MODEL}")
    
    # Initialize database components
    with MongoDBClient() as db_client:
        nodes_manager = NodesManager(db_client)
        
        # Execute commands based on arguments
        if args.stats:
            show_stats(nodes_manager)
        
        if args.sample_with:
            show_sample_nodes(nodes_manager, args.sample_with, with_embeddings=True)
        
        if args.sample_without:
            show_sample_nodes(nodes_manager, args.sample_without, with_embeddings=False)
        
        if args.clear_embeddings:
            clear_all_embeddings(nodes_manager, args.confirm)
        
        # If no specific command, show stats by default
        if not any([args.stats, args.sample_with, args.sample_without, args.clear_embeddings]):
            show_stats(nodes_manager)


if __name__ == "__main__":
    main()
