"""
Utility functions for embedding generation operations.
"""
import logging
from typing import Optional


def setup_logging(level: int = logging.INFO) -> None:
    """
    Set up logging configuration.
    
    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()],
    )


def log_progress(processed: int, total: int, item_name: str = "items") -> None:
    """
    Log a nicely formatted progress line with totals and remaining count.
    
    Args:
        processed: Number of items processed
        total: Total number of items
        item_name: Name of the items being processed (e.g., "nodes", "documents")
    """
    if total == 0:
        logging.info(f"No {item_name} to process")
        return
        
    remaining = total - processed
    percentage = (processed / total * 100)
    
    logging.info(
        "Processed %s / %s %s (%.2f%%) – %s left",
        processed,
        total,
        item_name,
        percentage,
        remaining,
    )


def log_embedding_stats(stats: dict) -> None:
    """
    Log embedding statistics in a formatted way.
    
    Args:
        stats: Dictionary containing embedding statistics
    """
    logging.info("=== Embedding Statistics ===")
    logging.info(f"Total nodes: {stats.get('total_nodes', 0)}")
    logging.info(f"Nodes with embeddings: {stats.get('nodes_with_embeddings', 0)}")
    logging.info(f"Nodes without embeddings: {stats.get('nodes_without_embeddings', 0)}")
    logging.info(f"Completion percentage: {stats.get('embedding_completion_percentage', 0):.2f}%")
    logging.info("=" * 30)


class ProgressTracker:
    """Track and log progress of long-running operations."""
    
    def __init__(self, total: int, item_name: str = "items", log_interval: int = 100):
        """
        Initialize progress tracker.
        
        Args:
            total: Total number of items to process
            item_name: Name of the items being processed
            log_interval: Log progress every N items
        """
        self.total = total
        self.item_name = item_name
        self.log_interval = log_interval
        self.processed = 0
        self.errors = 0
        
    def update(self, increment: int = 1) -> None:
        """
        Update progress counter.
        
        Args:
            increment: Number of items processed in this update
        """
        self.processed += increment
        
        if self.processed % self.log_interval == 0 or self.processed == self.total:
            log_progress(self.processed, self.total, self.item_name)
    
    def add_error(self) -> None:
        """Increment error counter."""
        self.errors += 1
    
    def get_summary(self) -> dict:
        """
        Get summary of processing results.
        
        Returns:
            Dictionary with processing summary
        """
        return {
            "total": self.total,
            "processed": self.processed,
            "errors": self.errors,
            "success_rate": ((self.processed - self.errors) / self.processed * 100) if self.processed > 0 else 0
        }
    
    def log_final_summary(self) -> None:
        """Log final processing summary."""
        summary = self.get_summary()
        logging.info(f"✅ Finished processing {summary['processed']} {self.item_name}")
        if summary['errors'] > 0:
            logging.warning(f"⚠️  {summary['errors']} errors occurred during processing")
            logging.info(f"Success rate: {summary['success_rate']:.2f}%")
