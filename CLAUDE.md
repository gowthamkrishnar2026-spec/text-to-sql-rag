# Text-to-SQL with RAG: project notes for Claude Code

College project (VIT Chennai): English question -> validated read-only SQL -> PostgreSQL -> table/chart.
RAG layer (Gemini embeddings + ChromaDB) sends only relevant tables and example queries to the model.
Read README.md first; backend/RAG.md covers retrieval details. Planned work: docs/ROADMAP.md (do Phase 0 first).

## Layout
- backend/app: FastAPI app. RAG code is app/services/rag_*.py, embedding_service.py, vector_store.py, prompt_builder.py.
- backend/tests: pytest suite (no API key or network needed). backend/benchmarks: evaluation scripts and saved results.
- frontend/: Next.js 16 dashboard. NOTE: the Docker frontend image is a baked build; rebuild with `bash scripts/update_ui.sh`.
- docs/paper: IEEE paper (docx + Overleaf zip). Review III submission is due 2 Nov 2026.

## Commands
- Run everything: `cp .env.example .env` (add GEMINI_API_KEY), then `docker compose up --build`
- Backend tests: `cd backend && PYTHONPATH=. python -m pytest -q`
- Full check: `bash scripts/verify.sh`

## Rules
- Never commit .env (it holds real API keys). Backend code is volume-mounted in Docker; restart is enough.
- The SQL validator must stay SELECT/WITH only, single statement.
- Paper numbers come from backend/benchmarks/*.json; keep README and paper in sync if results change.
