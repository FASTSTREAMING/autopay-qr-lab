#!/usr/bin/env bash
set -euo pipefail

systemctl daemon-reload
systemctl enable --now autopay-test.service
systemctl --no-pager status autopay-test.service
