#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

TASK_NAME="${1:-${AUTOPAY_TASKER_TASK:-}}"
if [ -z "$TASK_NAME" ]; then
  echo "Uso: ./scripts/run_tasker_direct.sh 'Nombre exacto de tarea'"
  echo "O exporta AUTOPAY_TASKER_TASK='Nombre exacto de tarea'"
  exit 1
fi

echo "Intentando ejecutar tarea Tasker directa:"
echo "  $TASK_NAME"
am broadcast \
  -a net.dinglisch.android.tasker.ACTION_TASK \
  --es task_name "$TASK_NAME"
