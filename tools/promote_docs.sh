#!/bin/bash

# Configuration
STAGING_DIR="docs/staging"
VENV_PATH=".venv/bin/activate"

echo ">>> Starting Folder-Aware Promotion"

# 1. Check if Staging is empty
if [ -z "$(ls -A $STAGING_DIR)" ]; then
   echo "--- Staging is empty. Nothing to promote."
   exit 0
fi

# 2. Route files based on Metadata
for file in "$STAGING_DIR"/*.md; do
    [ -e "$file" ] || continue
    
    # Extract the 'topic' value from YAML frontmatter
    TOPIC=$(grep "^topic:" "$file" | head -n 1 | awk '{print $2}' | tr -d "'\"")
    
    # Determine Destination Folder
    case "$TOPIC" in
        "opinions")
            DEST="docs/tn/opinions"
            ;;
        "county_legislative"|"county_executive"|"county_finance")
            DEST="docs/tn/county"
            ;;
        *)
            DEST="docs/tn/code"
            ;;
    esac

    mkdir -p "$DEST"
    echo ">>> Promoting $(basename "$file") to $DEST"
    mv "$file" "$DEST/"
done

# 3. Trigger the Indexer
if [ -f "indexer.py" ]; then
    echo ">>> Refreshing ChromaDB Index..."
    source $VENV_PATH
    python3 indexer.py
else
    echo "!!! Error: indexer.py not found."
    exit 1
fi

echo ">>> Promotion Complete. Run ./scripts/check_all.sh to verify."