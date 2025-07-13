#!/usr/bin/env python3
"""
Generate embeddings for nodes in MongoDB that don't have embeddings yet.
This script processes all nodes without embeddings and adds them using the configured model.
"""

import logging

from src import (
    embed_text,
    MongoDBClient,
    NodesManager,
    EMBEDDING_MODEL,
)
from src.embedding_utils import setup_logging, ProgressTracker, log_embedding_stats


def main() -> None:
    """Main function to generate embeddings for nodes without them."""
    # Set up logging
    setup_logging()
    
    # Log which model we're using
    logging.info(f"Using embedding model: {EMBEDDING_MODEL}")
    
    # Initialize database components
    with MongoDBClient() as db_client:
        nodes_manager = NodesManager(db_client)
        
        # Get initial statistics
        stats = nodes_manager.get_collection_stats()
        log_embedding_stats(stats)
        
        # Check if there are nodes to process
        total_nodes = stats["nodes_without_embeddings"]
        if total_nodes == 0:
            logging.info("✅ All nodes already have embeddings!")
            return
        
        # Initialize progress tracking (log every 10 nodes for better feedback)
        progress = ProgressTracker(total_nodes, "nodes", log_interval=10)
        
        # Process nodes without embeddings
        logging.info(f"Starting to process {total_nodes} nodes without embeddings...")
        
        nodes_iterator = nodes_manager.find_nodes_without_embeddings()
        
        for node in nodes_iterator:
            try:
                # Generate text content from the node
                input_text = node.generate_text_content()
                
                if not input_text.strip():
                    logging.warning(f"Node {node._id} has no text content, skipping")
                    progress.update()
                    continue
                
                # Generate embedding using the configured model
                embedding = embed_text(input_text)
                
                # Update the node in the database
                success = nodes_manager.update_node_embedding(node._id, embedding)
                
                if not success:
                    logging.error(f"Failed to update node {node._id} in database")
                    progress.add_error()
                
                progress.update()
                
            except Exception as exc:
                logging.exception(f"Failed to embed node {node._id}: {exc}")
                progress.add_error()
                progress.update()
        
        # Log final results
        progress.log_final_summary()
        
        # Get updated statistics
        final_stats = nodes_manager.get_collection_stats()
        log_embedding_stats(final_stats)


if __name__ == "__main__":
    main()

