#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

JOB_ID="${1:?uso: requeue_job.sh JOB_ID}"
SERVER_URL="${AUTOPAY_SERVER_URL:-http://127.0.0.1:8009}"

curl -sS -X POST "${SERVER_URL%/}/job/${JOB_ID}/reset"
printf '\n'
