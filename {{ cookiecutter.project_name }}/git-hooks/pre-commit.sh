#!/bin/sh
set -e

echo "Running pre-commit hook..."
eval persist-notebooks
eval git add -A  # this is added again since we are modifying a file during commit cycle and need to assure its staged