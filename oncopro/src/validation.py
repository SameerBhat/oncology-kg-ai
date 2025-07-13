"""
Validation utilities for the embedding system.
"""
import logging
import sys
from typing import List

from .config.settings import EMBEDDING_MODEL
from .embeddings.factory import EmbeddingModelFactory
from .database.client import MongoDBClient
from .database.operations import NodesManager


logger = logging.getLogger(__name__)


def validate_embedding_model() -> bool:
    """
    Validate that the embedding model specified in .env exists in our supported models.
    
    Returns:
        True if the model is supported, False otherwise
    """
    logger.info(f"Validating embedding model: {EMBEDDING_MODEL}")
    
    available_models = EmbeddingModelFactory.list_available_models()
    
    if EMBEDDING_MODEL not in available_models:
        logger.error(f"❌ Embedding model '{EMBEDDING_MODEL}' is not supported!")
        logger.error(f"Available models: {', '.join(available_models)}")
        logger.error("Please update your .env file with a supported EMBEDDING_MODEL")
        return False
    
    logger.info(f"✅ Embedding model '{EMBEDDING_MODEL}' is supported")
    return True


def validate_database_exists() -> bool:
    """
    Validate that the database exists and contains nodes.
    This checks if 'npm run convert-mm-db' has been run first.
    
    Returns:
        True if the database exists with nodes, False otherwise
    """
    logger.info("Validating database existence and node data...")
    
    try:
        with MongoDBClient() as db_client:
            nodes_manager = NodesManager(db_client)
            
            # Get collection stats
            stats = nodes_manager.get_collection_stats()
            total_nodes = stats["total_nodes"]
            
            if total_nodes == 0:
                logger.error("❌ No nodes found in the database!")
                logger.error("It appears the database is empty or doesn't exist.")
                logger.error("Please run 'npm run convert-mm-db' first to import the mind map data.")
                return False
            
            logger.info(f"✅ Database exists with {total_nodes} nodes")
            return True
            
    except Exception as exc:
        logger.error(f"❌ Failed to connect to database or check nodes: {exc}")
        logger.error("Please ensure MongoDB is running and accessible.")
        logger.error("Also run 'npm run convert-mm-db' to import the mind map data.")
        return False


def run_pre_embedding_checks() -> bool:
    """
    Run all pre-embedding validation checks.
    
    Returns:
        True if all checks pass, False if any check fails
    """
    logger.info("🔍 Running pre-embedding validation checks...")
    
    checks = [
        ("Embedding model validation", validate_embedding_model),
        ("Database existence validation", validate_database_exists),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        logger.info(f"Running {check_name}...")
        if not check_func():
            all_passed = False
        logger.info("")  # Add spacing between checks
    
    if all_passed:
        logger.info("✅ All validation checks passed! Ready to generate embeddings.")
    else:
        logger.error("❌ Some validation checks failed. Please fix the issues above before proceeding.")
    
    return all_passed
