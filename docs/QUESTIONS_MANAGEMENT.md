# Questions Management System

This document describes the questions management functionality that has been added to the OnCoPro system.

## Overview

The system now supports parsing questions from Excel files and storing them in MongoDB. The questions are stored in a collection called `questions` in the database specified by the `EMBEDDING_MODEL` environment variable.

## Files Modified/Created

### 1. `generate_questions.py`

Main script for parsing XLSX files and storing questions in MongoDB.

**Features:**

- **Idempotent by default**: Running the script multiple times will not create duplicate questions
- Automatically detects column names (supports various formats)
- Handles both English and German questions
- Batch insertion for better performance
- Comprehensive error handling and logging
- Supports clearing existing questions before insertion
- Option to force duplicate insertion when needed

**Usage:**

```bash
python generate_questions.py [options]
```

**Options:**

- `--file, -f`: Path to XLSX file (default: `oncopro_questions.xlsx`)
- `--sheet, -s`: Sheet name to read (default: `Sheet1`)
- `--clear`: Clear existing questions before inserting new ones
- `--force-duplicates`: Allow duplicate questions to be inserted (bypasses idempotent behavior)
- `--sample N`: Show N sample questions after processing
- `--verbose, -v`: Enable verbose logging

**Examples:**

```bash
# Parse default file and show 3 samples (idempotent)
python generate_questions.py --sample 3

# Parse custom file and clear existing questions
python generate_questions.py --file my_questions.xlsx --clear

# Parse with verbose logging (shows duplicate detection)
python generate_questions.py --verbose

# Force insertion of duplicates (non-idempotent)
python generate_questions.py --force-duplicates
```

### 2. Database Operations (`src/database/operations.py`)

Added `QuestionsManager` class for managing question operations.

**Methods:**

- `insert_question()`: Insert a single question
- `insert_questions_batch()`: Insert multiple questions (allows duplicates)
- `insert_questions_batch_idempotent()`: Insert multiple questions (skips duplicates)
- `question_exists()`: Check if a question already exists
- `get_existing_questions_set()`: Get all existing questions for efficient comparison
- `count_questions()`: Count total questions
- `clear_all_questions()`: Clear all questions
- `get_questions()`: Retrieve questions

### 3. Updated `tools/db_manager.py`

Extended database manager to support questions management.

**New Options:**

- `--questions-stats`: Show questions collection statistics
- `--questions-sample N`: Show N sample questions
- `--clear-questions`: Clear all questions from collection

**Examples:**

```bash
# Show both nodes and questions statistics (default)
python tools/db_manager.py

# Show 5 sample questions
python tools/db_manager.py --questions-sample 5

# Show questions statistics only
python tools/db_manager.py --questions-stats
```

## Excel File Format

The system expects an Excel file with the following structure:

### Supported Column Names

**English Questions:**

- `question_en`
- `Question (english)`
- `question_english`
- `english`
- `en`

**German Questions:**

- `question_de`
- `Question (german)`
- `question_german`
- `german`
- `de`

### Example Structure

```
| Question (english)                                    | Question (german)                                      |
|-------------------------------------------------------|--------------------------------------------------------|
| What is the standard classification of sarcomas?     | Wie erfolgt die Standardklassifikation von Sarkomen? |
| How is staging done for head and neck tumors?        | Wie erfolgt die Stadieneinteilung bei Kopf-Hals?     |
```

## Idempotent Behavior

### How It Works

The script is **idempotent by default**, meaning you can run it multiple times safely without creating duplicate questions. Here's how it works:

1. **Duplicate Detection**: Before inserting questions, the script checks existing questions in the database
2. **Efficient Comparison**: Uses a set-based approach to compare (question_en, question_de) tuples
3. **Smart Skipping**: Only inserts questions that don't already exist
4. **Detailed Reporting**: Provides counts of inserted vs. skipped questions

### Example Output

**First Run:**

```
2025-08-12 20:23:28,411 [INFO] Found 0 existing questions in collection
2025-08-12 20:23:28,411 [INFO] Inserted 13 new questions
2025-08-12 20:23:28,411 [INFO] Successfully inserted 13 new questions
```

**Second Run (Idempotent):**

```
2025-08-12 20:22:40,477 [INFO] Found 13 existing questions in collection
2025-08-12 20:22:40,478 [INFO] Skipped 13 duplicate questions
2025-08-12 20:22:40,478 [INFO] All questions already exist in the database - no new questions inserted
```

### Bypassing Idempotent Behavior

If you need to insert duplicates for testing or other purposes, use the `--force-duplicates` flag:

```bash
python generate_questions.py --force-duplicates
```

## Database Schema

### Questions Collection

Each question document has the following structure:

```json
{
  "_id": ObjectId("..."),
  "question_en": "English question text",
  "question_de": "German question text"
}
```

## Dependencies

### New Dependencies Added

- `pandas`: For Excel file reading
- `openpyxl`: For Excel file format support

These are automatically installed when running the script for the first time.

## Error Handling

The system includes comprehensive error handling for:

- Missing or invalid Excel files
- Incorrect column names or formats
- Database connection issues
- Empty or malformed data

## Integration

The questions management system is fully integrated with the existing OnCoPro architecture:

- Uses the same database configuration (`EMBEDDING_MODEL` environment variable)
- Follows the same logging patterns
- Uses the same MongoDB client and connection management
- Maintains consistency with existing code style and patterns

## Future Enhancements

Potential future improvements could include:

- Question embedding generation for semantic search
- Question categorization and tagging
- Multi-language support beyond English/German
- Question validation and deduplication
- Integration with the existing search functionality
