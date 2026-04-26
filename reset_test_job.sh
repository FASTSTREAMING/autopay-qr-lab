#!/usr/bin/env bash
set -euo pipefail

PORT="${AUTOPAY_TEST_PORT:-8009}"
curl -s -X POST "http://127.0.0.1:${PORT}/job/TEST-0001/reset"
printf '\n'
