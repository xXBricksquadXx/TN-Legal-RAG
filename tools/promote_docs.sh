#!/bin/bash

# Configuration
STAGING_DIR="docs/staging"
FINAL_DIR="docs/tn/code"
VENV_PATH=".venv/bin/activate"

echo ">>> Starting Promotion: Staging -> Production"

# 1. Check if Staging is empty
if [ -z "$(ls -A $STAGING_DIR)" ]; then
   echo "--- Staging is empty. Nothing to promote."
   exit 0
fi

# 2. Move files from Staging to Final
echo ">>> Moving files to $FINAL_DIR..."
mv $STAGING_DIR/*.md $FINAL_DIR/

# 3. Trigger the Indexer
if [ -f "indexer.py" ]; then
    echo ">>> Refreshing ChromaDB Index..."
    source $VENV_PATH
    python3 indexer.py
else
    echo "!!! Error: indexer.py not found in current directory."
    exit 1
fi

echo ">>> Promotion Complete. Your Handbook is now updated."
echo ">>> Run ./scripts/check_all.sh to verify the new 8/8 baseline."