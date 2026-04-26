#!/usr/bin/env bash
set -euo pipefail

REPO_NAME="${1:-autopay-qr-lab}"
VISIBILITY="${2:-private}"

if ! command -v gh >/dev/null 2>&1; then
  echo "Falta GitHub CLI (gh). Instala con:"
  echo "  sudo apt-get install -y gh"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Primero autentica GitHub:"
  echo "  gh auth login"
  exit 1
fi

cd "$(dirname "${BASH_SOURCE[0]}")/.."
git init
git add .
git commit -m "Initial autopay QR lab" || true
gh repo create "$REPO_NAME" "--$VISIBILITY" --source . --remote origin --push

echo "Publicado en GitHub: $REPO_NAME"
