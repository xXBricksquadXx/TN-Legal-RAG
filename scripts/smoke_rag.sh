#!/usr/bin/env bash
set -euo pipefail
BASE=${1:-http://127.0.0.1:8000}

echo "Health:"
curl -s "$BASE/health" | jq

echo "Eligibility:"
curl -s -X POST "$BASE/query" -H 'content-type: application/json' \
  -d '{"q":"Who can request records under the TPRA?","topic":"sunshine"}' \
  | jq '.answer,.sources'

echo "TDOS:"
curl -s -X POST "$BASE/query" -H 'content-type: application/json' \
  -d '{"q":"Where do I submit a TPRA request to TDOS?","topic":"sunshine"}' \
  | jq '.answer,.sources'

echo "Fees:"
curl -s -X POST "$BASE/query" -H 'content-type: application/json' \
  -d '{"q":"What are copy charges and when is labor charged for TPRA requests?","topic":"sunshine"}' \
  | jq '.answer,.sources'
