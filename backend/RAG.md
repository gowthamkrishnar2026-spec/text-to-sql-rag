# RAG for Text-to-SQL

Two retrieval steps run before the Gemini call:
1. **Schema retrieval** – each table is embedded as a "card"; top-k tables plus FK-linked tables go into the prompt. Enabled by default for every database (`RAG_SCHEMA_MIN_TABLES=1`); raise it to skip retrieval on small schemas.
2. **Example retrieval** – similar question->SQL pairs (Spider train + `app/data/rag_examples.json`) are inserted as few-shot examples.

Any retrieval failure falls back to the old behaviour (full schema + built-in examples). The response has a `rag` field showing what happened.

## Setup (from backend/)
    pip install -r requirements.txt
    PYTHONPATH=. python scripts/build_rag_index.py --check-store      # verifies ChromaDB, no API calls
    PYTHONPATH=. python scripts/build_rag_index.py --dry-run
    PYTHONPATH=. python scripts/build_rag_index.py --max-examples 300 # resumable; rerun if quota hits
    PYTHONPATH=. python scripts/build_rag_index.py --stats

## Benchmarks
    PYTHONPATH=. python benchmarks/rag_spider_eval.py --dry-run
    PYTHONPATH=. python benchmarks/rag_spider_eval.py --limit 100     # baseline/schema/examples/both on Spider dev
    PYTHONPATH=. python benchmarks/rag_ablation.py --limit 5          # needs backend running; A..E on the 30-question suite

## Tests
    PYTHONPATH=. python -m pytest tests/test_rag.py

## Settings (.env / config.py)
GEMINI_EMBEDDING_MODEL, RAG_EMBEDDING_DIM, RAG_VECTOR_BACKEND (chroma|memory), RAG_STORE_PATH,
RAG_SCHEMA_ENABLED/MIN_TABLES/TOP_K/MAX_TABLES, RAG_EXAMPLES_ENABLED/TOP_K, SCHEMA_INCLUDE_KEYS.

## Project-only examples (default)
`RAG_EXAMPLE_SOURCES=project` (default) retrieves only this app's own examples from `app/data/rag_examples.json`
(52 question->SQL pairs over the 11 tables, each verified by executing against the sample database).
Spider pairs stay in the index but are ignored. Set `RAG_EXAMPLE_SOURCES=project,spider` to allow them.
After editing rag_examples.json, re-run `PYTHONPATH=. python scripts/build_rag_index.py --max-examples 0`
(embeds only the new examples), then `docker compose restart backend`.

## Schema annotations (descriptions + allowed values)
The prompt schema now carries a one-line description per table (app/data/schema_descriptions.json) and the allowed
values of small-choice text columns (e.g. orders.status IN ('Completed','Processing','Shipped')), read from the database
and cached for 5 minutes. Settings: SCHEMA_DESCRIPTIONS, SCHEMA_VALUE_HINTS, SCHEMA_HINT_MAX_VALUES (all default on).
Turn both off to get the previous prompt. Preview the exact schema text the model sees:
    PYTHONPATH=. python -c "from app.db.session import format_schema_for_prompt as f; print(f())"
