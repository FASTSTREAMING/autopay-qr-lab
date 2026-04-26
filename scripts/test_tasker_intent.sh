#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ACTION="${AUTOPAY_TASKER_INTENT_ACTION:-com.autopay.qr.RUN}"

echo "Probando broadcast para Tasker:"
echo "  Action: $ACTION"
am broadcast \
  -a "$ACTION" \
  --es job_id "TASKER-TEST" \
  --es payment_id "TASKER-TEST" \
  --es tx_code "TASKER-TEST" \
  --es qr_path "/sdcard/Download/PAY-TEST-0001.png"
