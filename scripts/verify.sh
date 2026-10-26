#!/bin/bash
# One-command health check before recording the demo or pushing to GitHub.
#   bash scripts/verify.sh
set -e
cd "$(dirname "$0")/.."
echo "== 1/4 Backend tests =="
(cd backend && source venv/bin/activate && PYTHONPATH=. python -m pytest -q)
echo; echo "== 2/4 Frontend lint =="
(cd frontend && npm run lint)
echo; echo "== 3/4 Frontend production build =="
(cd frontend && npm run build >/dev/null && echo "build OK")
echo; echo "== 4/4 Docker Compose file =="
docker compose config -q && echo "compose OK"
echo; echo "All checks passed."
