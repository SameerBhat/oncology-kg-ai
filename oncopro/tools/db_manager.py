#!/usr/bin/env python3
"""
Database management utility for viewing embedding statistics and managing the nodes collection.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
from typing import Optional

from src import (
    MongoDBClient, 
    NodesManager,
    QuestionsManager,
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


def show_questions_stats(questions_manager: QuestionsManager) -> None:
    """Show questions collection statistics."""
    total_questions = questions_manager.count_questions()
    print(f"\n📊 Questions Collection Statistics:")
    print("=" * 40)
    print(f"Total questions: {total_questions}")


def show_sample_questions(questions_manager: QuestionsManager, limit: int = 5) -> None:
    """Show sample questions from the collection."""
    questions = questions_manager.get_questions(limit=limit)
    
    if not questions:
        print("No questions found in the collection.")
        return
    
    print(f"\nSample {min(limit, len(questions))} questions from the collection:")
    print("=" * 60)
    
    for i, q in enumerate(questions, 1):
        question_id = q.get('_id')
        question_en = q.get('question_en', '')
        question_de = q.get('question_de', '')
        
        print(f"{i}. ID: {question_id}")
        print(f"   EN: {question_en}")
        print(f"   DE: {question_de}")
        print()


def clear_all_questions(questions_manager: QuestionsManager, confirm: bool = False) -> None:
    """Clear all questions from the collection."""
    if not confirm:
        response = input("⚠️  This will remove ALL questions from the collection. Are you sure? (yes/no): ")
        if response.lower() != 'yes':
            print("Operation cancelled.")
            return
    
    count_deleted = questions_manager.clear_all_questions()
    print(f"✅ Cleared {count_deleted} questions from the collection.")


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
    parser.add_argument("--questions-stats", action="store_true", help="Show questions collection statistics")
    parser.add_argument("--questions-sample", type=int, metavar="N", help="Show N sample questions")
    parser.add_argument("--clear-questions", action="store_true", help="Clear all questions from collection")
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
        questions_manager = QuestionsManager(db_client)
        
        # Execute commands based on arguments
        if args.stats:
            show_stats(nodes_manager)
        
        if args.sample_with:
            show_sample_nodes(nodes_manager, args.sample_with, with_embeddings=True)
        
        if args.sample_without:
            show_sample_nodes(nodes_manager, args.sample_without, with_embeddings=False)
        
        if args.clear_embeddings:
            clear_all_embeddings(nodes_manager, args.confirm)
        
        if args.questions_stats:
            show_questions_stats(questions_manager)
        
        if args.questions_sample:
            show_sample_questions(questions_manager, args.questions_sample)
        
        if args.clear_questions:
            clear_all_questions(questions_manager, args.confirm)
        
        # If no specific command, show stats by default
        if not any([args.stats, args.sample_with, args.sample_without, args.clear_embeddings,
                   args.questions_stats, args.questions_sample, args.clear_questions]):
            show_stats(nodes_manager)
            show_questions_stats(questions_manager)


if __name__ == "__main__":
    main()
