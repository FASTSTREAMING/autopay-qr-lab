#!/usr/bin/env bash
set -euo pipefail

PORT="${AUTOPAY_TEST_PORT:-8009}"
JOB_ID="${1:-TEST-0001}"
curl -s -X POST "http://127.0.0.1:${PORT}/job/${JOB_ID}/reset"
printf '\n'
