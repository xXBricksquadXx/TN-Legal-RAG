#!/usr/bin/env bash
set -euo pipefail
BASE=${1:-http://127.0.0.1:8000}

echo "Health:"
curl -s "$BASE/health" | jq

echo "Eligibility (TPRA):"
curl -s -X POST "$BASE/query" -H 'content-type: application/json' \
  -d '{"q":"Who can request records under the TPRA?"}' \
  | jq '.answer,.sources'

echo "TDOS:"
curl -s -X POST "$BASE/query" -H 'content-type: application/json' \
  -d '{"q":"Where do I submit a TPRA request to TDOS?"}' \
  | jq '.answer,.sources'

echo "Fees:"
curl -s -X POST "$BASE/query" -H 'content-type: application/json' \
  -d '{"q":"What are copy charges and when is labor charged for TPRA requests?"}' \
  | jq '.answer,.sources'

echo "Open Meetings (TOMA):"
curl -s -X POST "$BASE/query" -H 'content-type: application/json' \
  -d '{"q":"Can a county commission hold a closed executive session to discuss public business?"}' \
  | jq '.answer,.sources'

echo "Willful Denial & Attorney Fees:"
curl -s -X POST "$BASE/query" -H 'content-type: application/json' \
  -d '{"q":"If a county requires me to show up in person to request a public record, is that a willful denial that justifies attorney fees?"}' \
  | jq '.answer,.sources'