"""
Utility functions for embedding generation operations.
"""
import logging
import time
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
    """Track and log progress of long-running operations with time-based metrics."""
    
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
        self.start_time = time.time()
        
    def update(self, increment: int = 1) -> None:
        """
        Update progress counter and log detailed progress with timing.
        
        Args:
            increment: Number of items processed in this update
        """
        self.processed += increment
        
        if self.processed % self.log_interval == 0 or self.processed == self.total:
            self._log_detailed_progress()
    
    def _log_detailed_progress(self) -> None:
        """Log detailed progress with timing information."""
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        
        # Calculate metrics
        remaining_items = self.total - self.processed
        percentage = (self.processed / self.total * 100) if self.total > 0 else 0
        
        # Time calculations
        avg_time_per_item = elapsed_time / self.processed if self.processed > 0 else 0
        estimated_remaining_time = avg_time_per_item * remaining_items
        
        # Speed calculation (items per second)
        speed = self.processed / elapsed_time if elapsed_time > 0 else 0
        
        # Format time strings
        elapsed_str = self._format_time(elapsed_time)
        remaining_str = self._format_time(estimated_remaining_time)
        
        logging.info(
            "Progress: %d/%d %s (%.1f%%) | "
            "Speed: %.2f %s/sec | "
            "Avg: %.2fs/%s | "
            "Elapsed: %s | "
            "ETA: %s",
            self.processed,
            self.total,
            self.item_name,
            percentage,
            speed,
            self.item_name,
            avg_time_per_item,
            self.item_name.rstrip('s'),  # Remove 's' for singular form
            elapsed_str,
            remaining_str
        )
    
    def _format_time(self, seconds: float) -> str:
        """Format time in a human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
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
        """Log final processing summary with total time taken."""
        summary = self.get_summary()
        total_time = time.time() - self.start_time
        total_time_str = self._format_time(total_time)
        
        logging.info(f"✅ Finished processing {summary['processed']} {self.item_name} in {total_time_str}")
        if summary['errors'] > 0:
            logging.warning(f"⚠️  {summary['errors']} errors occurred during processing")
            logging.info(f"Success rate: {summary['success_rate']:.2f}%")
        
        # Final speed calculation
        avg_speed = summary['processed'] / total_time if total_time > 0 else 0
        logging.info(f"Average speed: {avg_speed:.2f} {self.item_name}/sec")
