#!/usr/bin/env bash
set -euo pipefail

BASE=${1:-http://127.0.0.1:8000}

echo ">>> Rebuilding index"
python indexer.py

echo
echo ">>> Smoke test"
scripts/smoke_rag.sh "$BASE"

echo
echo ">>> API eval"
python scripts/eval_api.py eval/cases.yaml
