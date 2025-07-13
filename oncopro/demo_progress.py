#!/usr/bin/env python3
"""Demo of the new progress tracking with time-based metrics."""

import time
import logging
from src.embedding_utils import setup_logging, ProgressTracker

def demo_progress_tracking():
    """Demonstrate the new progress tracking functionality."""
    # Set up logging
    setup_logging()
    
    # Demo with a small number of items
    total_items = 25
    tracker = ProgressTracker(total=total_items, item_name="nodes", log_interval=5)
    
    logging.info("🚀 Starting demo of new progress tracking...")
    logging.info(f"Processing {total_items} demo nodes with progress updates every 5 items")
    
    for i in range(total_items):
        # Simulate variable processing time (0.2-0.8 seconds per item)
        processing_time = 0.2 + (i % 3) * 0.2
        time.sleep(processing_time)
        
        # Simulate occasional errors
        if i == 7 or i == 18:
            tracker.add_error()
            
        tracker.update()
    
    tracker.log_final_summary()
    logging.info("✅ Demo completed!")

if __name__ == "__main__":
    demo_progress_tracking()
