#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -f "$ROOT/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
else
  echo "Create venv first: python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

export CHIPYIELD_DB_PATH="$ROOT/chipyield.duckdb"

echo "==> 1/4 Bronze ingestion"
python scripts/01_ingest_bronze.py --db "$CHIPYIELD_DB_PATH"

echo "==> 2/4 dbt run"
dbt run --profiles-dir .

echo "==> 3/4 dbt test"
dbt test --profiles-dir .

echo "==> 4/4 Train classifier + build RAG index"
python scripts/03_train_classifier.py --db "$CHIPYIELD_DB_PATH"
python scripts/04_rag_catalog.py --build

echo ""
echo "Pipeline complete."
echo "  DuckDB: $CHIPYIELD_DB_PATH"
echo "  Try RAG: python scripts/05_ask_catalog.py"
echo "  Try query: python scripts/04_rag_catalog.py --query 'what is the ML training table'"
