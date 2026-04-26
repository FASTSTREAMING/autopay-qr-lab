#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
.venv/bin/python scripts/import_latest_pending_order.py "$@"
