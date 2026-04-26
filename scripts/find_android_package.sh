#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

QUERY="${1:-takenos}"
cmd package list packages | grep -i "$QUERY" || true
