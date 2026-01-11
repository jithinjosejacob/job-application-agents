#!/bin/bash
# Run script for Resume Tailor AI

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set Python path to include project root
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Set library path for WeasyPrint (PDF generation)
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"

# Run the Streamlit app
cd "$SCRIPT_DIR"
streamlit run app/main.py "$@"
