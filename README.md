# Text-to-SQL with Retrieval-Augmented Schema Grounding

Ask a question in plain English, get a validated, read-only SQL query, run it on PostgreSQL and see the
result as a table and chart. A RAG layer (Gemini embeddings + ChromaDB) sends the model only the tables and
example queries that matter for the question instead of the whole schema.

**Team:** Gowthamkrishna R (23MIA1087) and Aakash R (23MIA1011), VIT Chennai.
**Paper:** [`docs/paper/`](docs/paper) (IEEE format, Word + Overleaf project).

| | |
|---|---|
| Frontend | Next.js 16, React 19, Tailwind CSS 4, Recharts |
| Backend | FastAPI, SQLAlchemy, sqlparse |
| Databases | PostgreSQL 16 (data and history), ChromaDB (vectors) |
| Model | Google Gemini (`gemini-flash-lite-latest`, with fallbacks), `gemini-embedding-001` (768-d) |

## How it works

```
question ──► embed ──► ChromaDB: top-k table cards (+ FK neighbours) and similar solved examples
                                   │
                                   ▼
              prompt = retrieved CREATE TABLE text + table notes + example Q→SQL pairs
                                   │
                                   ▼
                          Gemini  ──►  SQL
                                   │
                                   ▼
          validator (SELECT/WITH only, 16 blocked keywords, one statement)
                                   │
                                   ▼
                     PostgreSQL ──► table + chart + metrics
```

If retrieval fails (no key, quota, empty index) the app falls back to the full schema and built-in examples, so a
question is never lost because of the RAG layer. The API response includes a `rag` field showing exactly what was
retrieved, and the dashboard has a RAG switch to compare with and without it.

## Quick start (Docker)

Requirements: Docker Desktop and a free [Gemini API key](https://aistudio.google.com/apikey).

```bash
git clone <this-repo-url> && cd <repo-folder>
cp .env.example .env            # then put your key in GEMINI_API_KEY
docker compose up --build
```

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/api/health |

The database is created and seeded from `database/init.sql` (11 tables: university, e-commerce and corporate
domains). On the first start the backend embeds the 52 project example queries in the background (about a
minute); queries work immediately and use the built-in examples until that finishes.

Try: *"Top 5 products by total sales revenue"*, *"Average salary per corporate department"*,
*"Show students with CGPA greater than 8"*, *"List low stock products under 50 units"*.
Then try *"drop the students table"* to see the safety validator block it.

## Local development (without Docker)

Needs Python 3.11+, Node 20+ and a running PostgreSQL (for example `docker compose up postgres`).

```bash
# backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8000

# frontend (second terminal)
cd frontend
npm install
npm run dev
```

If PostgreSQL is not reachable, the backend falls back to a local SQLite copy so the app still starts.

## Tests

```bash
cd backend
PYTHONPATH=. python -m pytest -q        # 56 tests: SQL validator, RAG, schema hints, evaluation metrics
cd ../frontend && npm run lint && npm run build
```

The tests need no API key and no network.

## Evaluation

All scripts read `GEMINI_API_KEY` from `.env` and write JSON into `backend/benchmarks/`.

```bash
cd backend
PYTHONPATH=. python benchmarks/rag_ablation.py --configs B,C,D     # 30-question suite (backend must be running)
PYTHONPATH=. python benchmarks/rag_spider_eval.py --limit 40        # Spider dev subset (see datasets/README.md)
PYTHONPATH=. python benchmarks/run_benchmark.py                     # project accuracy benchmark
```

Results reported in the paper (own 30-question suite, n=30; Spider dev subset, n=32):

| Finding | Result |
|---|---|
| Schema notes + value hints | 86.7% → 96.7% execution accuracy |
| Table retrieval | prompt tokens 1,108 → 561 (−49%), table recall@4 = 1.00 |
| Spider subset, example retrieval | 62.5% → 71.9% |
| Past queries re-run | agreement with earlier correct answers 85.0% → 97.5% |
| Validator | 25/25 attacks blocked, 0/222 valid queries blocked |

At these sample sizes the accuracy differences are not statistically significant; the paper reports confidence
intervals and says so. Table retrieval cost two questions on the small 11-table schema (departments vs
corp_departments are near-duplicates), and the paper discusses this openly.

## API

| Endpoint | Description |
|---|---|
| `POST /api/query` | Question → SQL → validation → execution → chart hints (optional `use_schema_rag` and `use_example_rag` switches) |
| `POST /api/generate-sql` | Question → SQL only |
| `POST /api/execute-query` | Validate and run a SQL string |
| `GET /api/schema` | Live schema (tables, columns, keys) |
| `GET /api/history` | Query history |
| `POST /api/export` | CSV, Excel or PDF export |
| `GET /api/health` | Database and model status |
| `GET /api/rag/status` | Index sizes and retrieval settings |
| `GET /api/rag/ablation` | Latest ablation results shown in the dashboard |
| `GET/POST /api/rag/history-eval[/run]` | Re-run past queries with RAG on and off |
| `GET/POST /api/benchmarks[/run]` | Benchmark results and runner |

## Repository layout

```
backend/            FastAPI app (app/), RAG code (app/services/rag_*.py), tests/, benchmarks/, scripts/
frontend/           Next.js dashboard (src/app pages, src/components)
database/init.sql   Schema and seed data
docker/             Dockerfiles
docker-compose.yml  postgres + backend + frontend
datasets/           Spider download instructions and loader (data not stored in Git)
docs/               Paper, review reports, project notes
scripts/            Helper scripts (rebuild UI, run RAG checks)
```

More detail on the retrieval layer is in [`backend/RAG.md`](backend/RAG.md).

## Configuration

Everything is set in `.env` (see `.env.example`). Only `GEMINI_API_KEY` is required. The RAG settings
(`RAG_SCHEMA_TOP_K`, `RAG_EXAMPLES_TOP_K`, …) are optional.

## Troubleshooting

* **UI did not change after editing the frontend:** the Docker image contains a built copy of the UI. Run
  `bash scripts/update_ui.sh`.
* **429 / quota errors:** the free Gemini tier is rate limited; the client tries fallback models, then reports the error.
* **Port 5432 already in use:** stop your local PostgreSQL or change the port mapping in `docker-compose.yml`.

## License

MIT, see [LICENSE](LICENSE).
