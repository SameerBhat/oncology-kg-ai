#!/usr/bin/env python3
"""Test script for the new ProgressTracker."""

from src.embedding_utils import ProgressTracker
import time

def test_progress_tracker():
    """Test the new progress tracker implementation."""
    print("Testing new progress tracker...")
    
    # Test with 50 items, logging every 10 items
    tracker = ProgressTracker(total=50, item_name='test_nodes', log_interval=10)
    
    for i in range(50):
        time.sleep(0.1)  # Simulate processing time
        tracker.update()
    
    tracker.log_final_summary()

if __name__ == "__main__":
    test_progress_tracker()
