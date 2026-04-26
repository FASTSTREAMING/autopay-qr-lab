#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

SERVER_URL="${AUTOPAY_SERVER_URL:-}"
if [ -z "$SERVER_URL" ]; then
  echo "Falta AUTOPAY_SERVER_URL."
  echo 'Ejemplo: export AUTOPAY_SERVER_URL="http://100.108.186.83:8009"'
  exit 1
fi

echo "Server: $SERVER_URL"
echo "Device: ${AUTOPAY_DEVICE_ID:-android-test-1}"
echo

echo "1) Probando health..."
curl -m 10 -sS "${SERVER_URL%/}/health"
printf '\n\n'

echo "2) Probando jobs..."
curl -m 10 -sS "${SERVER_URL%/}/jobs"
printf '\n\nOK\n'
