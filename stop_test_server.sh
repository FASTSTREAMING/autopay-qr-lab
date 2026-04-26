#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ -f logs/autopay_test_server.pid ]; then
  PID="$(cat logs/autopay_test_server.pid)"
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    echo "Servidor detenido. PID: $PID"
  fi
  rm -f logs/autopay_test_server.pid
fi

pkill -f 'uvicorn server.autopay_test_server:app' 2>/dev/null || true
