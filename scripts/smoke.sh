#!/usr/bin/env bash
set -euo pipefail
curl -s http://127.0.0.1:8000/health | jq '.embed,.max_distance' \
&& echo "— fees —" \
&& curl -s -X POST http://127.0.0.1:8000/query -H 'content-type: application/json' \
  -d '{"q":"What are copy charges and when is labor charged for TPRA requests?","topic":"sunshine"}' | jq '.answer,.sources' \
&& echo "— 404(b) —" \
&& curl -s -X POST http://127.0.0.1:8000/query -H 'content-type: application/json' \
  -d '{"q":"What must a Tennessee court find to admit 404(b) other-acts evidence?","topic":"bar"}' | jq '.answer,.sources'
