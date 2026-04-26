#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
mkdir -p logs

PORT="${AUTOPAY_TEST_PORT:-8009}"

if ss -ltn | grep -q ":${PORT} "; then
  echo "El puerto ${PORT} ya esta en uso. Si el servidor ya esta corriendo, prueba:"
  echo "  ./check_test_server.sh"
  exit 0
fi

nohup .venv/bin/uvicorn server.autopay_test_server:app --host 0.0.0.0 --port "$PORT" \
  > "logs/autopay_test_server.log" 2>&1 &

echo $! > logs/autopay_test_server.pid
echo "Servidor iniciado en segundo plano. PID: $(cat logs/autopay_test_server.pid)"
echo "Health:"
sleep 1
curl -s "http://127.0.0.1:${PORT}/health"
printf '\n'
