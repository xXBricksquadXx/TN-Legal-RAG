#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/check_all.sh
#   ./scripts/check_all.sh http://127.0.0.1:8000
#
# What it does:
#   1) Rebuilds index (.chroma)
#   2) Restarts FastAPI/uvicorn to ensure it loads the fresh index
#   3) Runs smoke test
#   4) Runs eval suite

BASE="${1:-http://127.0.0.1:8000}"
export BASE

PIDFILE=".api.pid"

# Parse host/port from BASE (supports http://host:port)
HOST="$(python -c 'import os,urllib.parse;u=urllib.parse.urlparse(os.environ["BASE"]);print(u.hostname or "127.0.0.1")')"
PORT="$(python -c 'import os,urllib.parse;u=urllib.parse.urlparse(os.environ["BASE"]);print(u.port or (443 if u.scheme=="https" else 80))')"

kill_listeners() {
  # Kill anything listening on PORT (best effort)
  if command -v lsof >/dev/null 2>&1; then
    PIDS="$(lsof -t -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "${PIDS}" ]]; then
      echo ">>> Killing existing listener(s) on :$PORT -> ${PIDS}"
      kill ${PIDS} 2>/dev/null || true
      sleep 0.5
    fi
  fi

  # Also kill tracked PID, if present
  if [[ -f "$PIDFILE" ]]; then
    OLD_PID="$(cat "$PIDFILE" 2>/dev/null || true)"
    if [[ -n "${OLD_PID}" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
      echo ">>> Killing prior API pid ${OLD_PID}"
      kill "$OLD_PID" 2>/dev/null || true
      sleep 0.5
    fi
    rm -f "$PIDFILE"
  fi
}

wait_for_health() {
  echo ">>> Waiting for API health at ${BASE}/health"
  for _ in $(seq 1 80); do
    if curl -fsS "${BASE}/health" >/dev/null 2>&1; then
      echo ">>> API is up"
      return 0
    fi
    sleep 0.25
  done
  echo "ERROR: API did not become healthy at ${BASE}/health" >&2
  return 1
}

cleanup() {
  if [[ -f "$PIDFILE" ]]; then
    PID="$(cat "$PIDFILE" 2>/dev/null || true)"
    if [[ -n "${PID}" ]] && kill -0 "$PID" 2>/dev/null; then
      echo ">>> Stopping API (pid ${PID})"
      kill "$PID" 2>/dev/null || true
    fi
    rm -f "$PIDFILE"
  fi
}
trap cleanup EXIT

echo ">>> Rebuilding index"
python indexer.py

echo
echo ">>> Restarting API so it loads the fresh .chroma"
kill_listeners

# Start API in background (no reload, deterministic)
( uvicorn rag_api:app --host "$HOST" --port "$PORT" ) &
API_PID=$!
echo "$API_PID" > "$PIDFILE"

wait_for_health

echo
echo ">>> Smoke test"
scripts/smoke_rag.sh "$BASE"

echo
echo ">>> API eval"
python scripts/eval_api.py eval/cases.yaml
