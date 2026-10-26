# Comprehensive Codebase Analysis: AI Text-to-SQL System

This report provides an exhaustive, file-by-file analysis of the codebase, detailing exactly what is implemented (and what is not) based solely on the source code. This information is structured for easy extraction into a presentation (PPTX).

---

## 1. PURPOSE & OVERVIEW
**Problem Solved:** Non-technical users (like executives or analysts) often need data from relational databases but lack the SQL expertise to retrieve it.
**Solution (One-Paragraph Summary):** The project is a production-ready, full-stack web application that translates natural English questions into valid, secure SQL queries. It enforces strict security policies to prevent data modification, executes the generated query against a PostgreSQL database, and automatically visualizes the result set using interactive charts and data tables. 

---

## 2. ARCHITECTURE

### Folder Structure & Roles
*   `frontend/`: Contains the Next.js UI application. 
    *   `src/app/page.tsx`: The main interactive dashboard.
    *   `src/components/`: Reusable UI components (`Visualizer.tsx`, `SecurityRestrictionCard.tsx`, etc.).
*   `backend/`: Contains the FastAPI Python server.
    *   `app/api/endpoints.py`: Defines the REST API routes (e.g., `/api/query`).
    *   `app/services/`: Core logic modules (`ai_service.py`, `sql_validator.py`, `executor_service.py`).
    *   `app/db/session.py`: Database connection and schema reflection logic.
    *   `benchmarks/`: Python scripts for evaluating model accuracy (`run_benchmark.py`).
*   `database/`: Contains `init.sql`, which defines the database schema and seed data.
*   `docker/` & `docker-compose.yml`: Container orchestration files for deployment.

### System Connections & Data Flow
The system connects a React frontend to a FastAPI backend, which brokers communication between an external LLM API (Google Gemini) and a local PostgreSQL database.

**Request Flow Diagram:**
```text
1. User Input ("Top 5 products by revenue") 
   └── Frontend (Next.js Dashboard)
       └── POST /api/query
           └── Backend (FastAPI: endpoints.py)
               ├── 2. Database Schema Reflection (session.py)
               ├── 3. LLM API Call (ai_service.py -> Google Gemini API)
               │      └── Returns Raw SQL String
               ├── 4. Security Validation (sql_validator.py)
               │      └── AST Parsing to block non-SELECT statements
               ├── 5. Query Execution (executor_service.py -> PostgreSQL)
               └── 6. Result & Chart Recommendation Generation
           ┌── Returns JSON (Columns, Rows, Visualization Config, Metrics)
       ┌── Frontend renders ResultsTable.tsx and Visualizer.tsx
```

---

## 3. CORE FEATURES

### Natural Language to SQL
*   **Schema Handling:** Handled in `backend/app/db/session.py` via the `inspect_db_schema()` function. It uses SQLAlchemy to dynamically read table names, column data types, and foreign keys directly from the database.
*   **Prompt Construction:** Handled in `backend/app/services/ai_service.py` via `format_schema_for_prompt()`. The schema is converted into a plain-text DDL representation and injected into the LLM system prompt alongside strict instructions to return JSON.
*   **Model Calls:** Executed in `backend/app/services/ai_service.py` using `requests.post()` to the `generativelanguage.googleapis.com` Gemini endpoint. 

### SQL Security & Validation
*   **AST Parser:** Located in `backend/app/services/sql_validator.py` (`sanitize_and_validate_sql()`). It uses the `sqlparse` library to build an Abstract Syntax Tree of the generated query.
*   **Blocked Statements:** It explicitly blocks `DROP`, `DELETE`, `UPDATE`, `ALTER`, `TRUNCATE`, `INSERT`, and multiple statements (semicolon injection). 
*   **Guardrail Behavior:** If a destructive command is detected, a `SQLValidationError` is raised. The AI service intercepts this in `_convert_to_safe_alternative()` and dynamically converts the destructive query into a safe `SELECT` preview (e.g., converting `DELETE FROM users` to `SELECT * FROM users`). The frontend then displays a red `SecurityRestrictionCard.tsx` refusing the action but offering the safe preview.

### Execution, Visualization, & Export
*   **Execution:** `backend/app/services/executor_service.py` executes the validated SQL string using SQLAlchemy's `text()` construct against the PostgreSQL pool.
*   **Visualization:** The executor analyzes the returned columns (`_recommend_visualization()`). If it detects numeric columns, it recommends a chart type (Bar, Line, Pie, Area) based on the column headers (e.g., "date" triggers a Line chart). The frontend `Visualizer.tsx` uses `recharts` to render it.
*   **Export:** `backend/app/services/export_service.py` uses `pandas` and `reportlab` to convert the query results into downloadable CSV, Excel (`.xlsx`), or PDF files.

### Telemetry & Caching
*   **History Logging:** The `_db_insert_history()` function in `endpoints.py` logs every user prompt, generated SQL, row count, execution latency, and success/block status to the `query_history` PostgreSQL table.
*   **Schema Caching:** To prevent database overload, `session.py` implements a 60-second TTL in-memory cache (`_schema_cache_ttl = 60.0`) for the reflected database schema.

---

## 4. DATABASE & DATA

*   **Database Engine:** PostgreSQL (with an automatic fallback to local SQLite defined in `initialize_engine()` if Postgres is unreachable).
*   **Vector/RAG Capabilities:** **None.** There is no Vector database, no embedding generation, and no Retrieval-Augmented Generation (RAG) code in this repository. The entire schema is small enough that it is passed via simple string concatenation into the LLM context.
*   **Schemas & Seed Data:** The database is initialized via `database/init.sql` with three distinct domains inspired by the Spider dataset:
    1.  **University:** `students`, `departments`, `instructors`, `courses`, `enrollments`.
    2.  **E-Commerce:** `customers`, `products`, `orders`, `order_items`.
    3.  **Corporate:** `corp_departments`, `employees`.

---

## 5. TECH STACK

**Frontend (`frontend/package.json`):**
*   **Framework:** Next.js 16 (React 19)
*   **Styling:** Tailwind CSS (v4)
*   **Components:** Lucide React (Icons), Recharts (Data Visualization)
*   **Networking:** Axios

**Backend (`backend/requirements.txt`):**
*   **Language:** Python 3.11+
*   **Framework:** FastAPI, Uvicorn
*   **Database:** SQLAlchemy (ORM), psycopg2-binary (PostgreSQL Driver)
*   **Security & Utilities:** sqlparse (AST parsing), pandas, openpyxl, reportlab (Exports)

**Configuration (`.env`):**
*   Requires Database credentials: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_SERVER`, `POSTGRES_PORT`, `POSTGRES_DB`
*   Requires AI API keys: `GEMINI_API_KEY` (and optionally `GEMINI_MODEL`)

---

## 6. HOW TO RUN

To run the project locally via Docker, execute the following commands in the root directory:

```bash
# 1. Copy the example environment variables
cp .env.example .env

# 2. Add your GEMINI_API_KEY to the .env file

# 3. Build and launch the containerized application
docker compose up -d --build
```
Once running, the UI is accessible at `http://localhost:3000` and the API docs at `http://localhost:8000/docs`.

---

## 7. TESTS & EVALUATION

*   **Security Tests:** A Pytest suite exists (`backend/tests/test_sql_validator.py`) to verify that the AST parser successfully blocks `DROP`, `DELETE`, and SQL injection attempts.
*   **Accuracy Benchmarks:** The `backend/benchmarks/` directory contains custom evaluation scripts (`run_benchmark.py`). It tests 30 hand-crafted domain questions from `benchmark_suite.json`. 
*   **Measured Results:** The code actively logs Execution Accuracy (Spider EA), Column Match rate, and Generation Success. The most recent JSON run logged an **Execution Accuracy of ~76.7%** and an **Average Latency of ~15,000ms** (15 seconds) due to Gemini API processing time. These metrics are dynamically parsed and displayed on the frontend at `http://localhost:3000/benchmarks`.

---

## 8. STATUS & GAPS

**Completed Features:**
*   End-to-End translation, execution, visualization, and history logging.
*   Robust AST-based SQL security validation.
*   Dynamic schema reflection.

**Critical Gaps vs. Documentation Claims:**
*   **Hugging Face ML Models:** The `README.md` explicitly claims the project uses "Hugging Face Transformers (`SQLCoder` / `T5`)". **This is false.** There is zero machine learning inference code in the backend, and `torch`/`transformers` are entirely absent from `requirements.txt`. The system relies *exclusively* on the external Google Gemini API (`generativelanguage.googleapis.com`).
*   **Schema Scale Handling:** The current architecture passes reflected DDL metadata directly into the Gemini LLM prompt as text. Because modern Gemini models support up to 1M–2M context tokens, extensive database schemas fit directly into context without needing complex Vector DB / RAG retrieval pipelines, eliminating retrieval loss.
*   **Spider Benchmark Dataset:** Both the official Yale Spider dataset and Hugging Face Spider datasets are locally integrated for accuracy evaluation.
