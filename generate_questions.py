#!/usr/bin/env python3
"""
Parse questions from XLSX file and store them in MongoDB.

This script reads questions from oncopro_questions.xlsx (Sheet1) 
which contains two columns: question_en and question_de.
The questions are stored in a MongoDB collection called 'questions'
in the database specified by the EMBEDDING_MODEL environment variable.

The script is idempotent by default - running it multiple times will not
create duplicate questions. Use --force-duplicates to override this behavior.
"""

import argparse
import logging
import sys
import pandas as pd
from pathlib import Path
from typing import List, Dict

from src import (
    MongoDBClient, 
    QuestionsManager,
    EMBEDDING_MODEL,
    setup_logging
)


def load_questions_from_xlsx(file_path: str, sheet_name: str = "Sheet1") -> List[Dict[str, str]]:
    """
    Load questions from an XLSX file.
    
    Args:
        file_path: Path to the XLSX file
        sheet_name: Name of the sheet to read (default: "Sheet1")
        
    Returns:
        List of dictionaries with 'question_en' and 'question_de' keys
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If required columns are missing
        Exception: For other pandas/openpyxl related errors
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"XLSX file not found: {file_path}")
    
    try:
        # Read the Excel file
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        logging.info(f"Loaded Excel file: {file_path}, Sheet: {sheet_name}")
        logging.info(f"Found {len(df)} rows and {len(df.columns)} columns")
        
        # Check if required columns exist
        # Try different possible column name variations
        column_mapping = {
            'question_en': None,
            'question_de': None
        }
        
        # Possible column names for English questions
        en_variations = ['question_en', 'Question (english)', 'question_english', 'english', 'en']
        # Possible column names for German questions  
        de_variations = ['question_de', 'Question (german)', 'question_german', 'german', 'de']
        
        # Find the actual column names
        for col in df.columns:
            col_lower = col.lower().strip()
            if col in en_variations or col_lower in [v.lower() for v in en_variations]:
                column_mapping['question_en'] = col
            elif col in de_variations or col_lower in [v.lower() for v in de_variations]:
                column_mapping['question_de'] = col
        
        # Check if we found both columns
        missing_mappings = [key for key, value in column_mapping.items() if value is None]
        if missing_mappings:
            available_columns = list(df.columns)
            raise ValueError(
                f"Could not find columns for: {missing_mappings}. "
                f"Available columns: {available_columns}. "
                f"Expected variations - English: {en_variations}, German: {de_variations}"
            )
        
        logging.info(f"Using column mapping: {column_mapping}")
        
        # Rename columns to standard names for easier processing
        df = df.rename(columns={
            column_mapping['question_en']: 'question_en',
            column_mapping['question_de']: 'question_de'
        })
        
        # Remove rows where both questions are empty/NaN
        df_clean = df.dropna(subset=['question_en', 'question_de'], how='all')
        
        if len(df_clean) < len(df):
            logging.warning(f"Removed {len(df) - len(df_clean)} rows with missing questions")
        
        # Convert to list of dictionaries
        questions = []
        for _, row in df_clean.iterrows():
            question_en = str(row['question_en']).strip() if pd.notna(row['question_en']) else ""
            question_de = str(row['question_de']).strip() if pd.notna(row['question_de']) else ""
            
            # Skip if both questions are empty
            if not question_en and not question_de:
                continue
                
            questions.append({
                'question_en': question_en,
                'question_de': question_de
            })
        
        logging.info(f"Successfully parsed {len(questions)} valid questions")
        return questions
        
    except Exception as e:
        logging.error(f"Error reading XLSX file: {e}")
        raise


def store_questions_in_db(questions: List[Dict[str, str]], questions_manager: QuestionsManager, 
                         clear_existing: bool = False, force_duplicates: bool = False) -> None:
    """
    Store questions in the MongoDB collection.
    
    Args:
        questions: List of question dictionaries
        questions_manager: QuestionsManager instance
        clear_existing: Whether to clear existing questions before inserting new ones
        force_duplicates: If True, allows duplicate insertions (bypasses idempotent behavior)
    """
    if clear_existing:
        count_deleted = questions_manager.clear_all_questions()
        logging.info(f"Cleared {count_deleted} existing questions from the collection")
    
    if not questions:
        logging.warning("No questions to store")
        return
    
    # Choose insertion method based on flags
    if force_duplicates:
        # Use the original batch insert method (allows duplicates)
        inserted_ids = questions_manager.insert_questions_batch(questions)
        logging.info(f"Successfully stored {len(inserted_ids)} questions in the database (duplicates allowed)")
    else:
        # Use the idempotent method (default behavior)
        result = questions_manager.insert_questions_batch_idempotent(questions)
        
        if result["inserted"] > 0:
            logging.info(f"Successfully inserted {result['inserted']} new questions")
        if result["skipped"] > 0:
            logging.info(f"Skipped {result['skipped']} duplicate questions")
        if result["inserted"] == 0 and result["skipped"] > 0:
            logging.info("All questions already exist in the database - no new questions inserted")
    
    # Show final statistics
    total_questions = questions_manager.count_questions()
    logging.info(f"Total questions in collection: {total_questions}")


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


def main():
    """Main function for processing questions."""
    parser = argparse.ArgumentParser(description="Parse questions from XLSX and store in MongoDB")
    parser.add_argument("--file", "-f", default="oncopro_questions.xlsx", 
                      help="Path to the XLSX file (default: oncopro_questions.xlsx)")
    parser.add_argument("--sheet", "-s", default="Sheet1", 
                      help="Sheet name to read (default: Sheet1)")
    parser.add_argument("--clear", action="store_true", 
                      help="Clear existing questions before inserting new ones")
    parser.add_argument("--force-duplicates", action="store_true",
                      help="Allow duplicate questions to be inserted (bypasses idempotent behavior)")
    parser.add_argument("--sample", type=int, metavar="N", 
                      help="Show N sample questions after processing")
    parser.add_argument("--verbose", "-v", action="store_true", 
                      help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    logging.info(f"Using database for embedding model: {EMBEDDING_MODEL}")
    logging.info(f"Questions will be stored in database: oncopro")
    
    try:
        # Load questions from XLSX
        questions = load_questions_from_xlsx(args.file, args.sheet)
        
        if not questions:
            logging.warning("No valid questions found in the file")
            return
        
        # Initialize database components - questions go to "oncopro" database
        with MongoDBClient(database_name="oncopro") as db_client:
            questions_manager = QuestionsManager(db_client)
            
            # Store questions in database
            store_questions_in_db(questions, questions_manager, args.clear, args.force_duplicates)
            
            # Show sample questions if requested
            if args.sample:
                show_sample_questions(questions_manager, args.sample)
            
        logging.info("Questions processing completed successfully")
        
    except FileNotFoundError as e:
        logging.error(f"File error: {e}")
        sys.exit(1)
    except ValueError as e:
        logging.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()