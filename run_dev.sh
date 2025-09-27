#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[ -f .venv/bin/activate ] && source .venv/bin/activate
export CHROMA_DIR=".chroma" CHROMA_COLLECTION="tn_legal" MAX_DISTANCE="0.75" TOP_K="6" CTX_CHAR_LIMIT="6000"
export OLLAMA_HOST="http://127.0.0.1:11434" OLLAMA_MODEL="qwen2.5:1.5b-instruct" OLLAMA_TEMPERATURE="0.1"
python indexer.py
exec uvicorn rag_api:app --host 127.0.0.1 --port 8000 --reload
