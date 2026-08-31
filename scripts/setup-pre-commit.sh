#!/bin/sh
set -eu

root="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$root"

if ! command -v pre-commit >/dev/null 2>&1; then
  echo "Installing pre-commit..."
  if command -v uv >/dev/null 2>&1; then
    uv tool install pre-commit
  else
    pip install pre-commit
  fi
fi

echo "Syncing backend dev tools..."
(cd backend && uv sync)

echo "Installing frontend dependencies..."
(cd frontend && npm install)

pre-commit install

echo "Done. Lint checks run automatically on git commit."
