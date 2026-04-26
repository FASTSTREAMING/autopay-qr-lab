#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

JOB_ID="${1:?uso: post_status.sh JOB_ID STATUS [mensaje]}"
STATUS="${2:?uso: post_status.sh JOB_ID STATUS [mensaje]}"
MESSAGE="${3:-}"
SERVER_URL="${AUTOPAY_SERVER_URL:-http://127.0.0.1:8009}"
DEVICE_ID="${AUTOPAY_DEVICE_ID:-android-test-1}"

curl -sS -X POST "${SERVER_URL%/}/job/${JOB_ID}/status" \
  -H 'Content-Type: application/json' \
  -d "{\"device_id\":\"${DEVICE_ID}\",\"status\":\"${STATUS}\",\"message\":\"${MESSAGE}\"}"
printf '\n'
