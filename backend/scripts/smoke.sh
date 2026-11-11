#!/usr/bin/env bash
# Run the whole pipeline with no API keys and no cost: mock models, a fictional
# five-page corpus, and a real Postgres + pgvector (docker compose up -d).
#
# Use it to confirm your install works before you spend anything. The numbers
# it prints are labelled MOCK and mean nothing.
set -euo pipefail
cd "$(dirname "$0")/.."

export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5433/eka}"
export TEST_DATABASE_URL="$DATABASE_URL"
export LLM_PROVIDER=mock LLM_MODEL=mock EMBED_PROVIDER=mock EMBED_MODEL=mock RERANK_PROVIDER=none
export HANDBOOK_CONTENT_DIR=tests/fixtures/content
export EKA_CORPUS_CONFIG=tests/fixtures/corpus.yaml
export EKA_GOLDEN_SET=tests/fixtures/golden_set.jsonl
export DB_SCHEMA=eka_smoke

echo "== tests"
python -m pytest -q
echo "== golden set vs corpus"
python -m scripts.validate_golden_set
echo "== experiments (mock)"
python -m evals.run_experiments --ingest-missing --no-judge | tail -12

cat <<'EOF'

Install works. To click through the UI on this fictional corpus, keep the
exports above in your shell and run:
  uvicorn eka.api:app --port 8000        (in backend/)
  npm install && npm run dev             (in web/)
EOF
