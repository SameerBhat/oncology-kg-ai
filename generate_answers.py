#!/usr/bin/env python3
"""
Generate answers by searching questions using embeddings and storing results in MongoDB.

This script:
1. Connects to the "oncopro" database
2. Retrieves all questions from the questions collection
3. For each question, uses the question_de (German) text to search using SearchManager
4. Stores the search results in the answers collection
5. Is idempotent - skips questions that already have answers for the current model

The answers collection schema:
- id: MongoDB ObjectId
- question_id: ID from the questions collection
- model_name: Current EMBEDDING_MODEL from environment
- nodes: Array of search result nodes with {_id, text, richText, notes, links, attributes, score}
- ordered_nodes: Empty array by default for manual reordering
- completed: Boolean, false by default

Usage:
    python generate_answers.py [options]

Examples:
    # Generate answers for all questions (top 10 results per question)
    python generate_answers.py

    # Generate answers with top 10 results per question
    python generate_answers.py --top-k 10

    # Show statistics after generation
    python generate_answers.py --stats

    # Clear existing answers for current model before generating new ones
    python generate_answers.py --clear-model

    # Show sample answers after generation
    python generate_answers.py --sample 3
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import logging
from typing import Optional, List, Dict, Any

from src import (
    MongoDBClient, 
    QuestionsManager,
    AnswersManager,
    SearchManager,
    EMBEDDING_MODEL,
    setup_logging
)


def show_stats(questions_manager: QuestionsManager, answers_manager: AnswersManager) -> None:
    """Show statistics for questions and answers."""
    total_questions = questions_manager.count_questions()
    answers_stats = answers_manager.get_answers_stats()
    
    print(f"\n📊 Generation Statistics:")
    print("=" * 40)
    print(f"Total questions: {total_questions}")
    print(f"Current model: {EMBEDDING_MODEL}")
    print(f"Total answers: {answers_stats['total_answers']}")
    
    if answers_stats['by_model']:
        print(f"\nAnswers by model:")
        for model, stats in answers_stats['by_model'].items():
            print(f"  {model}: {stats['count']} total, {stats['completed']} completed")
    else:
        print("No answers found in the collection.")


def show_sample_answers(answers_manager: AnswersManager, limit: int = 5) -> None:
    """Show sample answers from the collection."""
    answers = answers_manager.get_answers(model_name=EMBEDDING_MODEL, limit=limit)
    
    if not answers:
        print(f"No answers found for model {EMBEDDING_MODEL}.")
        return
    
    print(f"\nSample {min(limit, len(answers))} answers for model {EMBEDDING_MODEL}:")
    print("=" * 70)
    
    for i, answer in enumerate(answers, 1):
        answer_id = answer.get('_id')
        question_id = answer.get('question_id')
        nodes_count = len(answer.get('nodes', []))
        completed = answer.get('completed', False)
        
        print(f"{i}. Answer ID: {answer_id}")
        print(f"   Question ID: {question_id}")
        print(f"   Nodes count: {nodes_count}")
        print(f"   Completed: {'✅' if completed else '❌'}")
        
        # Show first node if available
        nodes = answer.get('nodes', [])
        if nodes:
            first_node = nodes[0]
            score = first_node.get('score', 0)
            text = first_node.get('text', '')[:100] + '...' if len(first_node.get('text', '')) > 100 else first_node.get('text', '')
            print(f"   Best match (score: {score:.3f}): {text}")
        print()


def clear_model_answers(answers_manager: AnswersManager, model_name: str, confirm: bool = False) -> None:
    """Clear all answers for the specified model."""
    if not confirm:
        response = input(f"⚠️  This will remove ALL answers for model '{model_name}'. Are you sure? (yes/no): ")
        if response.lower() != 'yes':
            print("Operation cancelled.")
            return
    
    count_deleted = answers_manager.clear_answers_by_model(model_name)
    print(f"✅ Cleared {count_deleted} answers for model {model_name}.")


def generate_answers_for_questions(
    questions_manager: QuestionsManager,
    answers_manager: AnswersManager,
    search_manager: SearchManager,
    top_k: int = 10,
    threshold: float = 0.0
) -> Dict[str, int]:
    """
    Generate answers for all questions by searching using the question_de text.
    
    Args:
        questions_manager: Manager for questions collection
        answers_manager: Manager for answers collection
        search_manager: Manager for search operations
        top_k: Number of top results to return per question
        threshold: Minimum similarity score threshold
        
    Returns:
        Dictionary with generation statistics
    """
    # Get all questions
    questions = questions_manager.get_questions()
    
    if not questions:
        logging.warning("No questions found in the collection")
        return {"processed": 0, "generated": 0, "skipped": 0, "errors": 0}
    
    logging.info(f"Found {len(questions)} questions to process")
    logging.info(f"Using model: {EMBEDDING_MODEL}, top_k: {top_k}, threshold: {threshold}")
    
    # Statistics
    processed = 0
    generated = 0
    skipped = 0
    errors = 0
    
    for question in questions:
        question_id = question['_id']  # Keep as ObjectId
        question_de = question.get('question_de', '').strip()
        question_en = question.get('question_en', '').strip()
        
        processed += 1
        
        # Skip if question_de is empty
        if not question_de:
            logging.warning(f"Question {question_id} has empty question_de, skipping")
            skipped += 1
            continue
        
        # Check if answer already exists for this question and model (idempotent)
        if answers_manager.answer_exists(question_id, EMBEDDING_MODEL):
            logging.debug(f"Answer already exists for question {question_id} with model {EMBEDDING_MODEL}, skipping")
            skipped += 1
            continue
        
        try:
            logging.info(f"Processing question {processed}/{len(questions)}: {question_de[:100]}...")
            
            # Search using the German question text
            search_results = search_manager.cosine_search(question_de, top_k=top_k, threshold=threshold)
            
            if not search_results:
                logging.warning(f"No search results found for question {question_id}")
                # Still create an entry with empty nodes
                search_results = []
            
            # Prepare nodes data for storage
            nodes_data = []
            for result in search_results:
                node_data = {
                    "id": result["nodeid"],
                    "text": result.get("text", ""),
                    "richText": result.get("richText", ""),
                    "notes": result.get("notes", ""),
                    "links": result.get("links", []),
                    "attributes": result.get("attributes", {}),
                    "score": result["score"]
                }
                nodes_data.append(node_data)
            
            # Insert answer into the collection
            answer_id = answers_manager.insert_answer(question_id, EMBEDDING_MODEL, nodes_data)
            
            generated += 1
            logging.info(f"Generated answer {answer_id} for question {question_id} with {len(nodes_data)} nodes")
            
        except Exception as e:
            logging.error(f"Error processing question {question_id}: {e}")
            errors += 1
            continue
    
    # Final statistics
    stats = {
        "processed": processed,
        "generated": generated,
        "skipped": skipped,
        "errors": errors
    }
    
    logging.info(f"Generation completed: {stats}")
    return stats


def main():
    """Main function for generating answers."""
    parser = argparse.ArgumentParser(description="Generate answers by searching questions using embeddings")
    parser.add_argument("--top-k", type=int, default=10, 
                        help="Number of top search results to store per question (default: 5)")
    parser.add_argument("--threshold", type=float, default=0.0,
                        help="Minimum similarity score threshold (default: 0.0)")
    parser.add_argument("--clear-model", action="store_true", 
                        help="Clear existing answers for current model before generating new ones")
    parser.add_argument("--stats", action="store_true", 
                        help="Show statistics after generation")
    parser.add_argument("--sample", type=int, metavar="N", 
                        help="Show N sample answers after generation")
    parser.add_argument("--confirm", action="store_true", 
                        help="Skip confirmation prompts")
    parser.add_argument("--verbose", "-v", action="store_true", 
                        help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    logging.info(f"Generating answers using embedding model: {EMBEDDING_MODEL}")
    logging.info(f"Target database: oncopro")
    logging.info(f"Top-k results per question: {args.top_k}")
    logging.info(f"Similarity threshold: {args.threshold}")
    
    try:
        # Initialize database components - all using "oncopro" database
        with MongoDBClient(database_name="oncopro") as questions_db_client:
            questions_manager = QuestionsManager(questions_db_client)
            answers_manager = AnswersManager(questions_db_client)
            
            # Clear existing answers for current model if requested
            if args.clear_model:
                clear_model_answers(answers_manager, EMBEDDING_MODEL, args.confirm)
            
            # Show initial stats
            if args.stats:
                show_stats(questions_manager, answers_manager)
        
        # Initialize search manager with the embedding model database
        with MongoDBClient() as embedding_db_client:
            search_manager = SearchManager(embedding_db_client)
            
            # Check if we have embeddings
            search_stats = search_manager.get_search_stats()
            if search_stats['total_nodes_with_embeddings'] == 0:
                logging.error("No nodes with embeddings found. Please run generate_db_embeddings.py first.")
                sys.exit(1)
            
            logging.info(f"Found {search_stats['total_nodes_with_embeddings']} nodes with embeddings for search")
            
            # Generate answers
            with MongoDBClient(database_name="oncopro") as questions_db_client:
                questions_manager = QuestionsManager(questions_db_client)
                answers_manager = AnswersManager(questions_db_client)
                
                generation_stats = generate_answers_for_questions(
                    questions_manager, 
                    answers_manager, 
                    search_manager,
                    top_k=args.top_k,
                    threshold=args.threshold
                )
                
                # Show results
                if generation_stats["generated"] > 0:
                    logging.info(f"✅ Successfully generated {generation_stats['generated']} new answers")
                if generation_stats["skipped"] > 0:
                    logging.info(f"⏭️  Skipped {generation_stats['skipped']} questions (already have answers or empty)")
                if generation_stats["errors"] > 0:
                    logging.warning(f"❌ Encountered {generation_stats['errors']} errors")
                
                # Show final statistics
                if args.stats:
                    show_stats(questions_manager, answers_manager)
                
                # Show sample answers if requested
                if args.sample:
                    show_sample_answers(answers_manager, args.sample)
        
        logging.info("Answer generation completed successfully")
        
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        logging.exception("Full error details:")
        sys.exit(1)


if __name__ == "__main__":
    main()
