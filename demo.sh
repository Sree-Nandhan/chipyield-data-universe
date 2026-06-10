#!/usr/bin/env bash
# Run from anywhere — resolves project path automatically
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ ! -f "$ROOT/.venv/bin/activate" ]; then
  echo "Creating Python 3.12 venv..."
  if command -v python3.12 >/dev/null 2>&1; then
    python3.12 -m venv .venv
  elif [ -x /opt/anaconda3/bin/python3.12 ]; then
    /opt/anaconda3/bin/python3.12 -m venv .venv
  else
    echo "ERROR: Python 3.12 required. Install it, then: python3.12 -m venv .venv"
    exit 1
  fi
  source .venv/bin/activate
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi

echo "Project: $ROOT"
echo ""
bash scripts/run_pipeline.sh
echo ""
echo "Starting RAG demo (type 'exit' to quit)..."
python scripts/05_ask_catalog.py
