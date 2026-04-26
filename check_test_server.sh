#!/usr/bin/env bash
set -euo pipefail

PORT="${AUTOPAY_TEST_PORT:-8009}"
curl -s "http://127.0.0.1:${PORT}/health"
printf '\n'
curl -s "http://127.0.0.1:${PORT}/jobs"
printf '\n'
