#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[ -f .venv/bin/activate ] && source .venv/bin/activate

# env
export CHROMA_DIR=".chroma"
export CHROMA_COLLECTION="tn_legal"
export EMBED_MODEL="sentence-transformers/all-MiniLM-L6-v2"
export TOP_K="24"
export CTX_CHAR_LIMIT="6000"
export MAX_DISTANCE="0.90"
export HYBRID_ALPHA="1.0"

export OLLAMA_HOST="http://127.0.0.1:11434"
export OLLAMA_MODEL="qwen2.5:1.5b-instruct"
export OLLAMA_TEMPERATURE="0.1"

# rebuild index
python indexer.py

# run API
exec uvicorn rag_api:app --host 127.0.0.1 --port 8000 --reload
