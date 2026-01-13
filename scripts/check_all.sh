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

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

# If BASE is like http://host:port, derive HOST/PORT from it
if [[ "$BASE" =~ ^https?://([^:/]+)(:([0-9]+))?(/.*)?$ ]]; then
  HOST="${BASH_REMATCH[1]}"
  if [[ -n "${BASH_REMATCH[3]:-}" ]]; then
    PORT="${BASH_REMATCH[3]}"
  fi
fi

API_PID=""

cleanup() {
  if [[ -n "${API_PID}" ]]; then
    echo ">>> Stopping API (pid ${API_PID})"
    kill "${API_PID}" 2>/dev/null || true
    wait "${API_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

stop_port_if_running() {
  local port="$1"
  local pids=""

  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -ti tcp:"${port}" || true)"
  elif command -v fuser >/dev/null 2>&1; then
    # fuser prints like "8000/tcp: 12345"
    pids="$(fuser -n tcp "${port}" 2>/dev/null || true)"
  fi

  if [[ -n "${pids}" ]]; then
    echo ">>> Stopping existing process(es) on port ${port}: ${pids}"
    kill ${pids} 2>/dev/null || true
    sleep 0.5
    kill -9 ${pids} 2>/dev/null || true
  fi
}

wait_for_health() {
  local url="$1"
  local tries="${2:-60}"
  local sleep_s="${3:-0.5}"

  if ! command -v curl >/dev/null 2>&1; then
    echo "ERROR: curl is required for health checks."
    exit 1
  fi

  for _ in $(seq 1 "${tries}"); do
    if curl -fsS "${url}" >/dev/null 2>&1; then
      return 0
    fi
    sleep "${sleep_s}"
  done

  echo "ERROR: API did not become healthy at ${url}"
  return 1
}

echo ">>> Rebuilding index"
python indexer.py

echo
echo ">>> Restarting API so it loads the fresh .chroma"
stop_port_if_running "${PORT}"

echo ">>> Waiting for API health at ${BASE}/health"
uvicorn rag_api:app --host "${HOST}" --port "${PORT}" >/tmp/tn_legal_rag_api.log 2>&1 &
API_PID="$!"

wait_for_health "${BASE}/health" 80 0.5
echo ">>> API is up"

echo
echo ">>> Smoke test"
./scripts/smoke_rag.sh "${BASE}"

echo
echo ">>> API eval"
python scripts/eval_api.py eval/cases.yaml