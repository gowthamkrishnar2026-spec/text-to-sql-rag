#!/bin/bash
# One-command RAG check: preview prompt schema, restart backend, run the ablation (B vs D).
# Usage:  bash scripts/check_rag.sh          (quick: 10 questions)    |    bash scripts/check_rag.sh full   (all 30)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
source venv/bin/activate

echo "== 1/4  Schema text the model will see (first lines) =="
PYTHONPATH=. python -c "from app.db.session import format_schema_for_prompt as f; print('\n'.join(f().splitlines()[:6]))"

echo; echo "== 2/4  Embedding any new project examples =="
PYTHONPATH=. python scripts/build_rag_index.py --max-examples 0

echo; echo "== 3/4  Restarting the Docker backend =="
(cd "$ROOT" && docker compose restart backend) || echo "(Docker not running - make sure the backend is up on port 8000)"
sleep 8

echo; echo "== 4/4  Ablation B (no examples) vs D (example retrieval) =="
if [ "$1" = "full" ]; then LIMIT=""; else LIMIT="--limit 10"; fi
PYTHONPATH=. python benchmarks/rag_ablation.py --configs B,D --delay 3 $LIMIT
