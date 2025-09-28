#!/usr/bin/env bash
set -euo pipefail
# stop any leftovers
pkill -f "uvicorn .* rag_api:app" 2>/dev/null || true
pkill -f "watchfiles" 2>/dev/null || true

# env (tight defaults)
export CHROMA_DIR=".chroma" CHROMA_COLLECTION="tn_legal"
export EMBED_MODEL="sentence-transformers/all-MiniLM-L6-v2"
export TOP_K=24 CTX_CHAR_LIMIT=6000 HYBRID_ALPHA=1.0
export MAX_DISTANCE=0.90
export OLLAMA_HOST="http://127.0.0.1:11434"
export OLLAMA_MODEL="qwen2.5:1.5b-instruct"
export OLLAMA_TEMPERATURE=0.1

# run without reloader to avoid port races
uvicorn rag_api:app --host 127.0.0.1 --port 8000 --no-access-log >/tmp/rag_api.log 2>&1 &
PID=$!
echo $PID > /tmp/rag_api.pid

# wait until healthy
for _ in {1..40}; do
  curl -sf http://127.0.0.1:8000/health >/dev/null && break
  sleep 0.25
done
curl -s http://127.0.0.1:8000/health | jq '.embed,.max_distance' || true
echo "API up (pid ${PID})"
