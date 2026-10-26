# Roadmap: from college project to real-world product

Every item lists **why**, **design**, **files**, **steps**, **tests** and **how to demo it**.
File paths are relative to the repo root. Effort: S = under a day, M = 1–3 days, L = a week or more.

Rules for every item:
- Keep the fallback promise: if a new feature fails, the query still works the old way.
- Add tests under `backend/tests/` (no API key or network needed) and run `bash scripts/verify.sh`.
- If a change moves accuracy, re-run `scripts/check_schema_rag.sh`, then update `docs/paper` and the README table.

---

## Phase 0: before the Review III deadline (2 Nov)

| # | Item | Effort |
|---|---|---|
| 0.1 | Fix the table-retrieval dip | S |
| 0.2 | Explain the 83.3% dashboard run | S |
| 0.3 | SQL self-correction retry | S |
| 5 | Safe execution (read-only role, timeout, LIMIT, EXPLAIN) | S–M |
| 6a | Confidence badge + thumbs up/down | S–M |
| 2a | Business glossary (JSON version) | M |
| 10a | GitHub Actions CI | S |

Then: re-run the benchmarks, update the paper, and record the demo video.

### 0.1 Fix the table-retrieval dip (S)
**Why:** schema retrieval scored 90.0% vs 96.7% with the full schema; CORP_008 picked `departments` instead of
`corp_departments` (card similarity 0.90).
**Steps**
1. In `backend/app/data/schema_descriptions.json`, make the two descriptions clearly different:
   `departments` = "University academic departments (building, budget) that instructors and courses belong to."
   `corp_departments` = "Company business units (Sales, Engineering…) that employees work in; use for salary/employee questions."
2. Set `RAG_SCHEMA_TOP_K` to 5 in `backend/app/core/config.py` (still under `RAG_SCHEMA_MAX_TABLES=6`).
3. Run `bash scripts/check_schema_rag.sh` twice (to see the noise) and record both runs.
**Test:** add a case in `tests/test_rag.py` asserting that "average salary per department" retrieves `corp_departments`
(using the memory store with fake embeddings, as the existing tests do).

### 0.2 Explain the 83.3% run (S)
Compare `backend/app/data/benchmark_rag_on.json` with the 96.7% ablation run case by case: list the failed IDs,
check for 429/quota errors (infrastructure failures, not wrong SQL), and note the n. Write the answer in one paragraph in
`docs/PROJECT_DOSSIER.md` so you can answer it in the viva.

### 0.3 SQL self-correction retry (S)
**Why:** many failures are SQL that errors (wrong column, type mismatch); the database error message tells the model
exactly what to fix.
**Design:** in `/api/query` (`backend/app/api/endpoints.py`), if `executor_service.execute_query` returns a database
error (not a validator block), call the model once more with the original prompt plus:
`The previous SQL failed with: <error>. Return a corrected query.` Validate and execute again. Maximum one retry.
**Files:** `services/prompt_builder.py` (new `build_repair_prompt`), `services/ai_service.py` (new `repair_sql`),
`api/endpoints.py`. Return `"repaired": true` and the first SQL in the response; show a small "auto-fixed" tag in the UI
(`frontend/src/app/page.tsx`).
**Settings:** `SQL_REPAIR_ENABLED=true`, `SQL_REPAIR_MAX_RETRIES=1`.
**Tests:** a fake LLM that returns broken SQL and then fixed SQL → one retry, result returned; a validator block → no retry.
**Metric for the paper:** execution accuracy with and without repair, plus the repair success rate.

---

## 1. Connect any database (L)
**Why:** customers want it on *their* data. This is the biggest step from demo to product.
**Design**
- New table `connections(id, name, dialect, dsn_encrypted, created_by, created_at)` in the app's own Postgres.
  Encrypt the DSN with Fernet (key from the `APP_SECRET_KEY` env var). Never return it to the frontend.
- `backend/app/db/registry.py`: `get_engine(connection_id)` caches one SQLAlchemy engine per connection.
  `db/session.py` keeps the current demo engine as connection `demo`.
- Schema reflection already exists in `db/session.py`; make it take an engine. Use the RAG `namespace` parameter
  (it already exists in `RagRuntime.prepare`) set to the connection id, so each database gets its own table cards.
- Dialects: Postgres first, then MySQL (`pymysql`), then Snowflake (`snowflake-sqlalchemy`). Pass the dialect into the
  prompt ("Write PostgreSQL/MySQL SQL").
**Endpoints:** `POST /api/connections` (test the connection, then save), `GET /api/connections`, `DELETE /api/connections/{id}`,
`POST /api/connections/{id}/reindex`. Add `connection_id` to `ProcessQueryRequest`.
**Frontend:** a "Databases" page (add, test, delete) and a database picker in the Navbar.
**Tests:** connect to a temporary SQLite file, reflect it, retrieve its tables, query it.
**Demo:** connect a Spider database live and ask a question about it.

## 2. Business glossary / semantic layer
### 2a. JSON version (M), in Phase 0
**Why:** users say "revenue" or "active customer", not column names.
**Design:** `backend/app/data/glossary.json`, entries like
`{"term": "active customer", "definition": "customer with an order in the last 90 days",
"sql_hint": "customer_id IN (SELECT customer_id FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL '90 days')",
"tables": ["customers", "orders"]}`.
Embed each entry as a card in a `glossary` collection (same `vector_store.py`). In `RagRuntime.prepare`, retrieve the top 3
terms; add their tables to the selected tables and a `Business definitions:` block to the prompt.
**Files:** `services/rag_service.py` (new `GlossaryIndex`), `services/prompt_builder.py`, `rag_bootstrap.py` (index on first run).
Write 10–15 terms for the demo database.
**Tests:** the glossary block appears in the prompt and its tables are forced into the schema.
### 2b. Editable version (M), later
Store the terms in Postgres, add an admin page to edit them, and re-embed on save.

## 3. Login and access control (L)
**Design**
- Auth: email + password with JWT (`python-jose`, `passlib[bcrypt]`), or Google sign-in. Tables `users` and `roles`.
- Policy per role: allowed tables and blocked columns, e.g. `analyst: {deny_columns: ["employees.salary"]}`.
- Enforce in three places:
  1. Retrieval: only cards of allowed tables can be retrieved (filter in `SchemaIndex.retrieve`).
  2. Validator: parse referenced tables and columns with sqlparse; reject anything outside the policy.
  3. Database: map each role to a Postgres role with `GRANT SELECT` on allowed tables and row-level security policies.
     This is the real guarantee; the first two are for clear error messages.
**Frontend:** login page, token in an httpOnly cookie, role shown in the Navbar.
**Tests:** an analyst asking for salary gets a clear "not allowed" message; an admin gets the result.

## 4. Privacy protection (M)
**Design**
- Mark sensitive columns in a `pii.json` (`customers.email`, `customers.phone`, `employees.salary`), or detect them by
  name and regex.
- Value hints (`services/schema_hints.py`) must skip PII columns, so real values never go to Gemini.
- Mask PII in results in `executor_service.py` (`a***@gmail.com`) unless the role allows it.
- Add a "data sent to the model" panel in the UI listing exactly what left the server (schema text only).
**Tests:** prompt text contains no sample PII values; results are masked for the analyst role.

## 5. Safe execution on large data (S–M), in Phase 0
**Design**
1. **Read-only role:** add `CREATE ROLE text2sql_reader LOGIN PASSWORD ...; GRANT SELECT ON ALL TABLES ...` to
   `database/init.sql`, and use it for `executor_service` (separate `READER_DSN` setting). The history writer keeps the
   normal user.
2. **Timeout:** `SET LOCAL statement_timeout = '5s'` inside the transaction in `executor_service.execute_query`.
3. **Row limit:** if the query has no `LIMIT`, wrap it: `SELECT * FROM (<sql>) AS q LIMIT 1000`.
   Tell the user when the results were cut.
4. **Cost check:** run `EXPLAIN (FORMAT JSON)` first; if the estimated rows exceed `MAX_ESTIMATED_ROWS` (for example
   1,000,000), return `needs_confirmation` and show a "This query scans ~N rows, run anyway?" dialog.
**Files:** `services/executor_service.py`, `core/config.py`, `database/init.sql`, `frontend/src/app/page.tsx`.
**Tests:** `pg_sleep` is already blocked; also test `generate_series(1,1e8)` hitting the timeout, and LIMIT wrapping.
**Demo:** run a huge cross join and show it stopped after 5 seconds.

## 6. Human review and feedback loop
### 6a. Confidence badge + thumbs (S–M), in Phase 0
- **Confidence:** compute from the top table score, the top example score and whether a repair was needed.
  High = top table ≥ 0.75 and top example ≥ 0.80; otherwise Medium or Low. Return `confidence` in `/api/query`.
  Show a coloured badge; for Low, add "Please check this SQL".
- **Feedback:** table `feedback(id, history_id, rating, corrected_sql, created_at)` and `POST /api/feedback`.
  Thumbs up/down under each result.
### 6b. Learning from feedback (M), later
- A thumbs-up whose SQL ran becomes a new example: append it to the index with `source="feedback"`, after checking that
  its question is not a near-duplicate (similarity under 0.95).
- A corrected SQL from an analyst is saved the same way, marked `source="analyst"`.
- Track accuracy before and after; this is a strong "system improves with use" graph.

## 7. Audit logs and monitoring (M)
**Design:** extend `query_history` with `user_id, connection_id, model, prompt_tokens, output_tokens, cost_usd,
retrieval_ms, llm_ms, db_ms, confidence, repaired, status`. Gemini returns the token counts; `llm_client.py` already
reads `prompt_tokens`.
**Dashboard page** (`frontend/src/app/monitoring`): queries per day, success rate, p50/p95 latency, cost per day and per
user, slowest queries, most common failures.
**Optional:** structured JSON logs and an OpenTelemetry exporter for Grafana.

## 8. Follow-up questions (M)
**Design:** send `conversation_id` with each query; keep the last 3 turns (question + SQL) in memory or Postgres.
Before retrieval, rewrite the follow-up into a standalone question with one short LLM call
("only for 2024" + previous turn → "total sales by region for 2024"), then run the normal pipeline.
Add the previous SQL to the prompt as context.
**UI:** chat-style thread on the dashboard with a "New question" button.
**Tests:** a fake LLM confirms the rewrite is used for retrieval.

## 9. Meet users where they work (M)
- **Slack bot:** a Slack Bolt app (`integrations/slack_bot.py`) with `/ask <question>`; it calls `/api/query` and replies
  with the SQL, a small table, and a link to the chart.
- **Scheduled reports:** table `schedules(id, user_id, question, cron, email)`; APScheduler runs each one and emails a
  CSV or PDF (the export service already exists).

## 10. Production deployment
### 10a. CI (S), in Phase 0
`.github/workflows/ci.yml`: on push, Python 3.11 → `pip install -r backend/requirements.txt` → `pytest`;
Node 20 → `npm ci && npm run lint && npm run build`. Add the badge to the README.
### 10b. Deployment (M), later
- Frontend on Vercel; backend on Render or Railway (Docker); Postgres on Neon or Supabase.
- Secrets in the host's secret manager, not `.env`. HTTPS by default on these hosts.
- Rate limiting with `slowapi` (for example 20 queries per minute per user). CORS restricted to the real domain.
- Persistent volume for `rag_store`, or move vectors to pgvector so there is one database fewer.
### 10c. Accuracy gate (S)
A nightly job runs the 30-question ablation with a real key; fail the job if accuracy drops more than 5 points from the
last saved run. This catches prompt changes that silently make results worse.

---

## Suggested order after the deadline
1. Item 6b (learning from feedback) and 7 (monitoring) – they reuse what Phase 0 builds.
2. Item 1 (any database) – the biggest product step.
3. Items 3 and 4 (access control, privacy) – needed before any real company data.
4. Items 8, 9, 10b – usability and deployment.

## What to say in an interview (FDE angle)
"I started with a Text-to-SQL demo, measured it honestly, then added what a customer deployment needs: connecting their
database, a business glossary so it speaks their language, database-level access control and PII masking, safe execution
limits, a feedback loop so it improves with use, and monitoring of accuracy and cost."
