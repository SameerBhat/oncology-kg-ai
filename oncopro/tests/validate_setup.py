#!/usr/bin/env python3
"""
Validation script to check system requirements before running embeddings.
Run this script to verify your setup is correct.
"""

import sys
from src.embedding_utils import setup_logging
from src.validation import run_pre_embedding_checks


def main() -> None:
    """Main function to run validation checks only."""
    setup_logging()
    
    print("🔍 OnCoPro Embedding System - Validation Check")
    print("=" * 50)
    
    if run_pre_embedding_checks():
        print("🎉 All checks passed! Your system is ready for embedding generation.")
        print("You can now run 'python generate_db_embeddings.py' safely.")
        sys.exit(0)
    else:
        print("⚠️  Please fix the issues above before running the embedding generation.")
        sys.exit(1)


if __name__ == "__main__":
    main()
