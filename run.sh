#!/bin/bash

# Simple wrapper script to run Python commands with the correct virtual environment
# Usage: ./run.sh script_name.py [args...]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"

if [ ! -f "$PYTHON_PATH" ]; then
    echo "Error: Python environment not found at $PYTHON_PATH"
    echo "Please ensure the virtual environment is set up correctly."
    exit 1
fi

# Check if script name is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 script_name.py [args...]"
    echo "Available scripts:"
    echo "  plot_ir_figures.py"
    echo "  generate_case_studies.py"
    echo "  compute_metrics.py"
    echo "  bootstrap_qrels_from_ordered.py"
    echo "  flatten_runs_from_answers.py"
    echo "  make_tables.py"
    echo "  wilcoxon_significance.py"
    exit 1
fi

# Run the Python script with the correct environment
cd "$SCRIPT_DIR"
exec "$PYTHON_PATH" "$@"
