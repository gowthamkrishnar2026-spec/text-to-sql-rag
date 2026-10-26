#!/bin/bash
# Schema-retrieval check: full schema (B) vs retrieved tables only (C), all 30 questions.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
source venv/bin/activate
echo "== Restarting backend (picks up the new schema-retrieval settings) =="
(cd "$ROOT" && docker compose restart backend) || echo "(start the backend on port 8000)"
sleep 8
echo "== B (all 11 tables) vs C (retrieved tables only) =="
PYTHONPATH=. python benchmarks/rag_ablation.py --configs B,C --delay 3
