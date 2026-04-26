#!/usr/bin/env bash
set -euo pipefail

journalctl -u autopay-test.service -n "${1:-80}" --no-pager
