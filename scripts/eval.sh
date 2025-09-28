#!/usr/bin/env bash
set -euo pipefail
echo "== health =="
curl -s http://127.0.0.1:8000/health | jq '.embed,.max_distance'
echo "== retrieval =="
scripts/eval_retrieval.py
echo "== api answers =="
scripts/eval_api.py
