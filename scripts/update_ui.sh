#!/bin/bash
# Rebuilds the frontend image (the UI is baked into it) and restarts the backend.
cd "$(dirname "$0")/.." || exit 1
docker compose restart backend
docker compose build frontend && docker compose up -d frontend
echo "Done. Open http://localhost:3000 and hard-refresh (Cmd+Shift+R)."
