#!/usr/bin/env bash
set -euo pipefail

systemctl stop autopay-test.service
systemctl --no-pager status autopay-test.service || true
