#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

pkg update -y
pkg install -y python git curl
python -m pip install -r requirements-termux.txt

termux-setup-storage || true

echo "OK: Termux listo."
echo "Ejecuta:"
echo "  export AUTOPAY_SERVER_URL=\"http://IP_TAILSCALE_VPS:8009\""
echo "  export AUTOPAY_DEVICE_ID=\"android-1\""
echo "  ./scripts/run_termux_worker.sh"
