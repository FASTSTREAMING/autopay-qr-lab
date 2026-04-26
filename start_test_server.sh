#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
exec .venv/bin/uvicorn server.autopay_test_server:app --host 0.0.0.0 --port "${AUTOPAY_TEST_PORT:-8009}"
