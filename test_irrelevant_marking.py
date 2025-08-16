#!/usr/bin/env python3
"""
Test script to demonstrate the irrelevant marking functionality.

This script shows how irrelevant nodes are handled in the qrels generation
and how they affect model evaluation metrics.
"""

import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List
from pymongo import MongoClient

# Mock functions that would normally be in your src module
def test_irrelevant_processing():
    """Test the irrelevant node processing logic."""
    
    # Sample data structures representing different annotation scenarios
    test_cases = [
        {
            "name": "Normal relevant nodes",
            "ordered_nodes": [
                {"node": {"id": "node1", "text": "relevant content"}, "original_index": 0},
                {"node": {"id": "node2", "text": "also relevant"}, "original_index": 1},
                {"node": {"id": "node3", "text": "somewhat relevant"}, "original_index": 2},
            ]
        },
        {
            "name": "Mixed relevant and irrelevant",
            "ordered_nodes": [
                {"node": {"id": "node1", "text": "relevant content"}, "original_index": 0},
                {"node": {"id": "node2", "text": "irrelevant content", "isIrrelevant": True}, "original_index": 1},
                {"node": {"id": "node3", "text": "also relevant"}, "original_index": 2},
            ]
        },
        {
            "name": "Duplicate and irrelevant nodes",
            "ordered_nodes": [
                {"node": {"id": "node1", "text": "relevant content"}, "original_index": 0},
                {"node": {"id": "node2", "text": "duplicate content", "isDuplicate": True}, "original_index": 1},
                {"node": {"id": "node3", "text": "irrelevant content", "isIrrelevant": True}, "original_index": 2},
                {"node": {"id": "node4", "text": "more relevant content"}, "original_index": 3},
            ]
        },
        {
            "name": "Manually added nodes",
            "ordered_nodes": [
                {"node": {"id": "node1", "text": "original relevant"}, "original_index": 0},
                {"node": {"id": "node_added", "text": "manually added relevant"}, "original_index": -1},
                {"node": {"id": "node2", "text": "original irrelevant", "isIrrelevant": True}, "original_index": 1},
            ]
        }
    ]
    
    def get_node_id(x: Any) -> str | None:
        """Extract node_id from OrderedNodeRecord, SavedNode, or raw id string."""
        if x is None:
            return None
        if isinstance(x, str):
            return x
        if isinstance(x, dict):
            if "node" in x:
                n = x["node"]
                if isinstance(n, str):
                    return n
                if isinstance(n, dict):
                    if "id" in n:
                        return str(n["id"])
            if "id" in x:
                return str(x["id"])
        return None

    def is_marked_duplicate(x: Any) -> bool:
        """True if the element itself or its nested node carries isDuplicate=True."""
        if not isinstance(x, dict):
            return False
        if x.get("isDuplicate") is True:
            return True
        n = x.get("node")
        if isinstance(n, dict) and n.get("isDuplicate") is True:
            return True
        return False

    def is_marked_irrelevant(x: Any) -> bool:
        """True if the element itself or its nested node carries isIrrelevant=True."""
        if not isinstance(x, dict):
            return False
        if x.get("isIrrelevant") is True:
            return True
        n = x.get("node")
        if isinstance(n, dict) and n.get("isIrrelevant") is True:
            return True
        return False
    
    print("Testing irrelevant node processing logic...\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case['name']}")
        print("-" * 50)
        
        items = test_case["ordered_nodes"]
        seen_ids = set()
        ranked_unique_ids = []
        irrelevant_ids = []
        skipped_duplicate = 0
        skipped_repeat = 0
        
        for elem in items:
            # Skip duplicates
            if is_marked_duplicate(elem):
                skipped_duplicate += 1
                continue
                
            nid = get_node_id(elem)
            if not nid:
                continue
                
            # Skip repeat IDs
            if nid in seen_ids:
                skipped_repeat += 1
                continue
                
            seen_ids.add(nid)
            
            # Separate relevant and irrelevant
            if is_marked_irrelevant(elem):
                irrelevant_ids.append(nid)
            else:
                ranked_unique_ids.append(nid)
        
        # Generate qrels (relevance scores)
        TOP_R = 3  # Top 3 are considered relevant
        qrels = {}
        
        # Assign positive relevance to top-ranked nodes
        for rank, nid in enumerate(ranked_unique_ids, start=1):
            rel = 1 if rank <= TOP_R else 0
            qrels[nid] = rel
        
        # Assign negative relevance to irrelevant nodes
        for nid in irrelevant_ids:
            qrels[nid] = -1
        
        print(f"  Original nodes: {len(items)}")
        print(f"  Skipped duplicates: {skipped_duplicate}")
        print(f"  Skipped repeats: {skipped_repeat}")
        print(f"  Relevant nodes: {ranked_unique_ids}")
        print(f"  Irrelevant nodes: {irrelevant_ids}")
        print(f"  Generated qrels: {qrels}")
        print()
    
    print("Impact on model evaluation:")
    print("- Relevant nodes (rank 1-3): +1 point each")
    print("- Relevant nodes (rank 4+): 0 points")
    print("- Irrelevant nodes: -1 point each")
    print("- This helps penalize models that retrieve irrelevant content")

if __name__ == "__main__":
    test_irrelevant_processing()
