# AUDIT DOSSIER: AI-POWERED TEXT-TO-SQL SEMANTIC QUERY SYSTEM

**Audit Date**: October 13, 2026  
**Auditor**: Antigravity Autonomous Codebase Auditor  
**Repository**: `/Users/gowthamkrishnar/Text To SQL`  
**Audit Standard**: Strict Fact Verification (Zero Speculation, All Claims Grounded in File Paths and Line Numbers)

---

## 1. ONE-PARAGRAPH SUMMARY

The project is a full-stack web application designed to translate natural English questions into SQL queries, validate them against a security policy, execute them on a relational database, and present results visually. The presentation layer is built with Next.js 16 (`frontend/package.json:L15`) and React 19 (`frontend/package.json:L16`), communicating via an Axios client (`frontend/src/services/api.ts:L5-10`) to a Python FastAPI backend (`backend/app/main.py:L6-10`). When a user submits a natural language question, the backend retrieves relational schema definitions using SQLAlchemy database inspection (`backend/app/db/session.py:L108-136`) and injects them into a prompt sent over HTTPS to the Google Gemini REST API (`backend/app/services/ai_service.py:L140-143`). The resulting SQL is checked by an Abstract Syntax Tree (AST) validation module utilizing `sqlparse` (`backend/app/services/sql_validator.py:L14-66`), which blocks destructive commands (`DROP`, `DELETE`, `UPDATE`, `ALTER`, `TRUNCATE`, multi-statement injections) and allows only `SELECT` or `WITH ... SELECT` queries. Permitted queries are executed against a PostgreSQL 16 database (or a local fallback SQLite file `backend/text2sql.db`, `backend/app/db/session.py:L37-51`) using SQLAlchemy (`backend/app/services/executor_service.py:L38-43`). Query results are categorized into numeric and string attributes to recommend dynamic Recharts visualizations (Bar, Line, Pie, Area) (`backend/app/services/executor_service.py:L93-132`), logged to an internal `query_history` database table (`backend/app/api/endpoints.py:L25-45`), and made exportable to CSV, Excel, or PDF formats (`backend/app/services/export_service.py:L6-76`).

---

## 2. PROBLEM & PURPOSE

* **Stated Problem**: "Non-technical users (like executives or analysts) often need data from relational databases but lack the SQL expertise to retrieve it."  
  *Evidence*: `codebase_analysis.md:L8`
* **Stated Primary Objective**: "To bridge the communication gap between non-technical stakeholders and complex relational databases by building an enterprise-grade, secure, semantic Text-to-SQL translation platform featuring real-time schema grounding, strict Abstract Syntax Tree (AST) safety guardrails, automated business intelligence charting, and multi-format data export."  
  *Evidence*: `REVIEW_II_REPORT.md:L25-26`
* **Stated Academic Context**: Academic project for Integrated M.Tech / M.Tech in Artificial Intelligence & Machine Learning (Data Engineering & Applied AI), Review Stage: Review II (30 Marks), candidate registration numbers `23MIA1087`, `23MIA1011`, `22MIA1174`.  
  *Evidence*: `REVIEW_II_REPORT.md:L10-20`

---

## 3. REPOSITORY MAP

```
Text To SQL/
├── .env.example                               # Environment variable template with redacted keys
├── docker-compose.yml                         # Multi-container orchestration (PostgreSQL, FastAPI, Next.js)
├── pyrightconfig.json                         # Pyright static typing configuration
├── README.md                                  # Repository overview and quickstart guide
├── REVIEW_II_REPORT.md                        # Academic review report for Review Stage II
├── codebase_analysis.md                       # Architecture notes and feature breakdown
├── generate_review2_doc.py                    # Script generating Microsoft Word (.docx) review documentation
├── Text_to_SQL_Review_II_Report.docx          # Generated Review II report document
├── Review_II_Report.docx                      # Generated Review II report document
├── scratch/
│   └── generate_benchmark_50.py              # One-off benchmark execution script generating 50-test-case report
├── docker/
│   ├── backend.Dockerfile                     # Docker container specification for Python 3.11 FastAPI backend
│   └── frontend.Dockerfile                    # Multi-stage Docker container specification for Next.js frontend
├── database/
│   └── init.sql                               # PostgreSQL DDL schema & multi-domain seed data (12 tables)
├── backend/
│   ├── requirements.txt                       # Python pip dependencies
│   ├── text2sql.db                            # SQLite database fallback populated with 12 tables (384 rows)
│   ├── app/
│   │   ├── main.py                            # FastAPI application entrypoint, CORS configuration, and router
│   │   ├── core/
│   │   │   └── config.py                      # Pydantic Settings reading environment variables
│   │   ├── db/
│   │   │   └── session.py                     # SQLAlchemy engine initialization, SQLite fallback, schema reflection
│   │   ├── api/
│   │   │   └── endpoints.py                   # REST API route handlers (/query, /schema, /history, /export, etc.)
│   │   ├── services/
│   │   │   ├── ai_service.py                  # Gemini API client, prompt assembler, destructive query interceptor
│   │   │   ├── sql_validator.py               # AST SQL security parser using sqlparse (SELECT-only guardrails)
│   │   │   ├── executor_service.py            # SQL query execution engine & heuristic chart recommender
│   │   │   ├── export_service.py              # Export generator for CSV (pandas), Excel (openpyxl), PDF (reportlab)
│   │   │   └── benchmark_service.py           # In-memory benchmark runner, polling state, and result persistence
│   │   └── data/
│   │       ├── benchmark.json                 # Persisted benchmark evaluation metrics and case results
│   │       └── benchmark_suite.json           # 30-case benchmark test suite definition
│   ├── benchmarks/
│   │   ├── benchmark_suite.json               # Canonical 30-case benchmark definition with gold SQL
│   │   ├── latest_benchmark.json              # Latest output report from benchmark suite run
│   │   ├── run_benchmark.py                   # Standalone CLI runner for 30 benchmark test cases
│   │   ├── spider_eval.py                     # Yale Spider benchmark evaluation script (Exact Match & Exec Accuracy)
│   │   ├── README.md                          # Benchmarking documentation
│   │   ├── benchmark_results_20261009_100007.json # Historic benchmark run result
│   │   ├── benchmark_results_20261009_100950.json # Historic benchmark run result (EA: 76.7%)
│   │   ├── benchmark_results_20261013_122403.json # Historic benchmark run result (EA: 56.7%)
│   │   ├── benchmark_results_20261013_122803.json # Historic benchmark run result (EA: 80.0%)
│   │   └── benchmark_results_20261013_123222.json # Historic benchmark run result (EA: 86.7%)
│   └── tests/
│       └── test_sql_validator.py              # Pytest unit tests for AST SQL validator (7 test cases)
├── datasets/
│   ├── __init__.py                            # Python package initialization
│   ├── loader.py                              # Yale Spider dataset loader & verification utility
│   ├── populate_full_dataset.py               # Script extracting Spider names and populating 100 students
│   ├── model_evaluation_50_test_cases.md      # Markdown report documenting 50 benchmark cases
│   ├── spider.zip                             # 95 MB compressed archive of official Yale Spider dataset
│   ├── spider/                                # Extracted Spider benchmark files:
│   │   ├── dev.json                           # 1,034 Spider evaluation questions across 20 databases
│   │   ├── dev_gold.sql                       # 1,034 gold standard SQL queries for dev set
│   │   ├── train_spider.json                  # 7,000 Spider training questions across 140 databases
│   │   ├── train_others.json                  # 1,659 training questions from external sources
│   │   ├── train_gold.sql                     # 8,659 gold standard SQL queries for training sets
│   │   ├── tables.json                        # Schema definitions for all 166 Spider databases
│   │   ├── README.txt                         # Official Spider dataset documentation and citations
│   │   └── database/                          # 166 directories each containing an individual SQLite database
│   └── huggingface_spider/                    # Parquet & JSON format Spider dataset (xlangai/spider):
│       ├── train.parquet                      # Hugging Face training split (7,000 examples, 831 KB)
│       ├── validation.parquet                 # Hugging Face validation split (1,034 examples, 126 KB)
│       ├── train.json                         # JSON format training split (7,000 examples, 7.88 MB)
│       ├── validation.json                    # JSON format validation split (1,034 examples, 1.14 MB)
│       └── README.md                          # Hugging Face dataset card and split metadata
└── frontend/
    ├── package.json                           # Frontend dependencies, scripts, and package versions
    ├── package-lock.json                      # Locked npm dependency tree
    ├── tsconfig.json                          # TypeScript compiler settings
    ├── next.config.ts                         # Next.js configuration
    ├── postcss.config.mjs                     # PostCSS plugins
    ├── eslint.config.mjs                      # ESLint configuration
    ├── public/                                # Static SVGs (file, globe, next, vercel, window)
    └── src/
        ├── app/
        │   ├── layout.tsx                     # Root layout component
        │   ├── page.tsx                       # Main interactive Text-to-SQL dashboard page
        │   ├── globals.css                    # Global CSS and custom styles
        │   ├── benchmarks/page.tsx            # Benchmarks & Records analytics page
        │   ├── history/page.tsx               # Chronological query execution history page
        │   ├── settings/page.tsx              # Database schema explorer page
        │   └── about/page.tsx                 # System architecture and information page
        ├── components/
        │   ├── Navbar.tsx                     # Top navigation bar with live status indicators
        │   ├── PromptInput.tsx                # Natural language prompt query input & sample prompt pills
        │   ├── SqlEditor.tsx                  # SQL code editor with real-time safety badge & execute action
        │   ├── ResultsTable.tsx               # Paginated, filterable tabular query output
        │   ├── Visualizer.tsx                 # Dynamic Recharts visualizer (Bar, Line, Pie, Area)
        │   ├── HistorySidebar.tsx             # Sidebar listing recent queries with click-to-rerun
        │   ├── ExportModal.tsx                # Modal offering CSV, Excel, and PDF downloads
        │   └── SecurityRestrictionCard.tsx    # Policy warning card with safe SELECT alternative execution
        ├── services/
        │   └── api.ts                         # Axios HTTP client and TypeScript interfaces
        └── data/
            └── benchmark.json                 # Bundled static benchmark dataset fallback
```

---

## 4. TECH STACK

All versions cited directly from package management files:

### 4.1 Backend (`backend/requirements.txt:L1-15`)
| Package | Version Constraint | Role in Repository |
| :--- | :--- | :--- |
| `fastapi` | `>=0.110.0` | Asynchronous REST API framework (`backend/app/main.py:L1`) |
| `uvicorn[standard]` | `>=0.28.0` | ASGI web server (`backend/app/main.py:L34`, `docker/backend.Dockerfile:L21`) |
| `sqlalchemy` | `>=2.0.28` | Relational database engine & schema reflection (`backend/app/db/session.py:L5`) |
| `psycopg2-binary` | `>=2.9.9` | PostgreSQL database adapter for Python (`backend/app/core/config.py:L19`) |
| `pydantic` | `>=2.6.4` | Data validation and request/response schemas (`backend/app/api/endpoints.py:L3`) |
| `pydantic-settings`| `>=2.2.1` | Environment variable management via `BaseSettings` (`backend/app/core/config.py:L2`) |
| `sqlparse` | `>=0.4.4` | Abstract Syntax Tree (AST) SQL parsing (`backend/app/services/sql_validator.py:L2`) |
| `requests` | `>=2.31.0` | Synchronous HTTP client calling Google Gemini API (`backend/app/services/ai_service.py:L4`) |
| `pandas` | `>=2.2.1` | Data manipulation for CSV and Excel generation (`backend/app/services/export_service.py:L3`) |
| `openpyxl` | `>=3.1.2` | Excel (.xlsx) file generation engine (`backend/app/services/export_service.py:L19`) |
| `reportlab` | `>=4.1.0` | PDF report document layout and generation (`backend/app/services/export_service.py:L26-30`) |
| `pytest` | `>=8.1.1` | Unit test execution (`backend/tests/test_sql_validator.py:L1`) |
| `httpx` | `>=0.27.0` | Async HTTP client dependency |
| `python-dotenv` | `>=1.0.1` | Reading `.env` files into environment (`backend/app/core/config.py:L5`) |

### 4.2 Frontend (`frontend/package.json:L11-30`)
| Package | Version in File | Role in Repository |
| :--- | :--- | :--- |
| `next` | `16.2.11` | React application framework (App Router) |
| `react` | `19.2.4` | Core UI component library |
| `react-dom` | `19.2.4` | React DOM renderer |
| `recharts` | `^3.10.0` | SVG chart visualizer: Bar, Line, Pie, Area (`frontend/src/components/Visualizer.tsx:L5-7`) |
| `axios` | `^1.18.1` | HTTP client for backend REST communication (`frontend/src/services/api.ts:L1`) |
| `lucide-react` | `^1.25.0` | Icon library for navigation, tables, and security alerts |
| `clsx` | `^2.1.1` | Utility for constructing conditional class name strings |
| `tailwind-merge` | `^3.6.0` | Utility for merging conflicting Tailwind classes |
| `tailwindcss` | `^4` (dev) | CSS utility framework (`frontend/package.json:L28`) |
| `@tailwindcss/postcss` | `^4` (dev) | PostCSS plugin for Tailwind v4 (`frontend/package.json:L22`) |
| `typescript` | `^5` (dev) | TypeScript type checking compiler |
| `eslint` | `^9` (dev) | JavaScript/TypeScript linter |
| `eslint-config-next` | `16.2.11` (dev) | Next.js ESLint configuration |

### 4.3 Containerization & Database Images
* **PostgreSQL**: `postgres:16-alpine` (`docker-compose.yml:L3`)
* **Backend Base Image**: `python:3.11-slim` (`docker/backend.Dockerfile:L1`)
* **Frontend Base Image**: `node:20-alpine` (`docker/frontend.Dockerfile:L2, L13`)

---

## 5. DATA SOURCES

### 5.1 Project Relational Databases (`database/init.sql` & `backend/text2sql.db`)
* **Origin**: Custom normalized relational schemas inspired by the Yale Spider benchmark domains, seeded with 384 rows.
* **Storage Format**: PostgreSQL 16 table relations (or local SQLite file `backend/text2sql.db` of size 188,416 bytes).
* **Schema Breakdown (12 Tables)**:
  1. `departments` (4 columns: `department_id` INT, `department_name` VARCHAR, `building` VARCHAR, `budget` REAL; Row Count: 5)
  2. `instructors` (5 columns: `instructor_id` INT, `name` VARCHAR, `email` VARCHAR, `department_id` INT, `salary` REAL; Row Count: 10)
  3. `students` (7 columns: `student_id` INT, `first_name` VARCHAR, `last_name` VARCHAR, `email` VARCHAR, `department_id` INT, `cgpa` REAL, `enrollment_year` INT; Row Count: 100)
  4. `courses` (6 columns: `course_id` INT, `course_code` VARCHAR, `course_title` VARCHAR, `credits` INT, `department_id` INT, `instructor_id` INT; Row Count: 15)
  5. `enrollments` (6 columns: `enrollment_id` INT, `student_id` INT, `course_id` INT, `grade` VARCHAR, `grade_point` REAL, `semester` VARCHAR; Row Count: 184)
  6. `customers` (5 columns: `customer_id` INT, `customer_name` VARCHAR, `city` VARCHAR, `country` VARCHAR, `created_at` TIMESTAMP; Row Count: 15)
  7. `products` (5 columns: `product_id` INT, `product_name` VARCHAR, `category` VARCHAR, `unit_price` REAL, `stock_quantity` INT; Row Count: 15)
  8. `orders` (5 columns: `order_id` INT, `customer_id` INT, `order_date` DATE, `total_amount` REAL, `status` VARCHAR; Row Count: 15)
  9. `order_items` (5 columns: `item_id` INT, `order_id` INT, `product_id` INT, `quantity` INT, `price_per_unit` REAL; Row Count: 6)
  10. `corp_departments` (3 columns: `dept_id` INT, `dept_name` VARCHAR, `location` VARCHAR; Row Count: 4)
  11. `employees` (6 columns: `emp_id` INT, `emp_name` VARCHAR, `job_title` VARCHAR, `dept_id` INT, `hire_date` DATE, `salary` REAL; Row Count: 15)
  12. `query_history` (7 columns: `id` INT, `prompt` TEXT, `sql_query` TEXT, `row_count` INT, `execution_time_ms` REAL, `status` VARCHAR, `created_at` TIMESTAMP; Row Count: dynamic audit log)
* **Sample Rows (`backend/text2sql.db`)**:
  * `departments`: `(1, 'Computer Science', 'Turing Hall', 1200000.0)`
  * `instructors`: `(1, 'Dr. Alan Turing', 'alan.turing@univ.edu', 1, 125000.0)`
  * `students`: `(1, 'Aarav', 'Sharma', 'aarav.sharma@student.edu', 1, 9.2, 2022)`

### 5.2 Yale Spider Benchmark Dataset (`datasets/spider/`)
* **Origin**: Official Yale NLP Spider Dataset (Tao Yu et al., EMNLP 2018), uncompressed from `datasets/spider.zip` (95 MB).
* **Format**: JSON annotation files, gold SQL files, and 166 standalone SQLite `.sqlite` databases.
* **Size & Volume**:
  * `datasets/spider/dev.json`: 3.5 MB, 1,034 question-SQL pairs across 20 databases (`datasets/loader.py:L149-167`).
  * `datasets/spider/train_spider.json`: 24 MB, 7,000 question-SQL pairs across 140 databases (`datasets/spider/README.txt:L10-12`).
  * `datasets/spider/train_others.json`: 8.1 MB, 1,659 question-SQL pairs across 6 databases (`datasets/spider/README.txt:L13-15`).
  * `datasets/spider/tables.json`: 792 KB, 166 relational database schema structures (`datasets/spider/README.txt:L20`).
  * `datasets/spider/dev_gold.sql`: 121 KB, 1,034 gold queries.
  * `datasets/spider/train_gold.sql`: 1.1 MB, 8,659 gold queries.
* **Sample Entry (`datasets/spider/dev.json`)**:
  ```json
  {
    "db_id": "concert_singer",
    "query": "SELECT count(*) FROM singer",
    "question": "How many singers do we have?"
  }
  ```

### 5.3 Hugging Face Spider Dataset (`datasets/huggingface_spider/`)
* **Origin**: Hugging Face dataset repository `xlangai/spider` (`datasets/loader.py:L57`).
* **Format**: Apache Parquet files and matching JSON serializations.
* **Size & Volume**:
  * `train.parquet`: 831,359 bytes (7,000 examples)
  * `validation.parquet`: 125,887 bytes (1,034 examples)
  * `train.json`: 7,886,630 bytes (7,000 examples)
  * `validation.json`: 1,140,590 bytes (1,034 examples)
* **Columns**: `db_id` (string), `query` (string), `question` (string), `query_toks` (list of strings), `query_toks_no_value` (list of strings), `question_toks` (list of strings).

### 5.4 Benchmark Test Suite (`backend/benchmarks/benchmark_suite.json`)
* **Origin**: Hand-crafted 30-case evaluation suite created for project accuracy benchmarking.
* **Format**: JSON array of test cases.
* **Size**: 30 objects, each specifying `id`, `domain` (University, E-Commerce, Corporate, Cross-Domain), `difficulty` (easy, medium, hard), `prompt`, `gold_sql`, `expected_columns`, and `expected_min_rows`.

---

## 6. DATA PIPELINE

The end-to-end processing pipeline executes through the following stages:

```
[User NL Prompt]
      │
      ▼
1. INGESTION: PromptInput.tsx ──(HTTP POST)──► endpoints.py::process_full_query()
      │
      ▼
2. SCHEMA GROUNDING: session.py::inspect_db_schema() & format_schema_for_prompt()
      │
      ▼
3. AI GENERATION: ai_service.py::generate_sql() ──(HTTPS)──► Google Gemini API
      │
      ▼
4. SECURITY & INTERCEPTION:
   ├── (Destructive intent?) ──► ai_service.py::_convert_to_safe_alternative()
   └── (Valid SELECT?)      ──► sql_validator.py::sanitize_and_validate_sql()
      │
      ▼
5. EXECUTION & TIMING: executor_service.py::execute_query() ──► PostgreSQL / SQLite
      │
      ▼
6. CHART INFERENCE: executor_service.py::_recommend_visualization()
      │
      ▼
7. AUDIT LOGGING: endpoints.py::_db_insert_history() ──► query_history Table
      │
      ▼
8. PRESENTATION: ResultsTable.tsx & Visualizer.tsx (Recharts)
      │
      ▼
9. EXPORT (Optional): export_service.py (CSV / Excel / PDF)
```

### Step 1: User Ingestion
* **Location**: `frontend/src/components/PromptInput.tsx:L22-26` -> `frontend/src/services/api.ts:L52-55` -> `backend/app/api/endpoints.py:L144-156`
* **Function**: `processTextToSqlQuery()` sends `{"prompt": "<natural language text>"}` via HTTP POST to `/api/query`. Handled by `process_full_query(request: ProcessQueryRequest)`.

### Step 2: Dynamic Schema Grounding
* **Location**: `backend/app/db/session.py:L96-165`
* **Function**: `inspect_db_schema()` uses SQLAlchemy's `inspect(engine)` to reflect table names, column names, column data types, and foreign key relations. Results are cached in `_schema_cache` with a 60-second TTL (`_SCHEMA_CACHE_TTL = 60.0`, `session.py:L17`). `format_schema_for_prompt()` formats the schema into DDL `CREATE TABLE` definitions.

### Step 3: Prompt Construction & LLM Generation
* **Location**: `backend/app/services/ai_service.py:L72-175`
* **Function**: `TextToSQLAIService.generate_sql(prompt)` constructs a system instruction containing the reflected DDL schema, security rules ("strictly enforces READ-ONLY access"), domain mapping guidelines, and output formatting instructions requiring ```sql code fences. It dispatches a JSON payload with `temperature: 0.0` and `maxOutputTokens: 2048` to `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}` across a candidate fallback list (`gemini-flash-lite-latest`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3.6-flash`, `gemini-flash-latest`).

### Step 4: Destructive Query Interception & AST Validation
* **Location**: `backend/app/services/ai_service.py:L195-230` & `backend/app/services/sql_validator.py:L14-66`
* **Function**:
  1. `ai_service.py` evaluates the prompt and output against `DESTRUCTIVE_PROMPT_PATTERN` (`\b(delete|drop|truncate|alter|remove|wipe|purge|clear\s+table|destroy|update|insert)\b`) and `FORBIDDEN_KEYWORDS`. If detected, `_convert_to_safe_alternative()` converts the destructive query into an equivalent safe `SELECT` preview (e.g. `DELETE FROM students WHERE cgpa < 7` -> `SELECT * FROM students WHERE cgpa < 7;`) and returns a blocked payload (`violation_type: "DESTRUCTIVE_OPERATION_RESTRICTED"`).
  2. For non-blocked queries, `sanitize_and_validate_sql()` in `sql_validator.py` cleans code fences, parses the statement using `sqlparse.parse()`, rejects queries containing multiple semicolon-separated statements, validates that the first statement begins with `SELECT` or `WITH`, flattens tokens to verify that no token matches `FORBIDDEN_KEYWORDS`, and normalizes trailing semicolons.

### Step 5: Database Execution & Telemetry Measurement
* **Location**: `backend/app/services/executor_service.py:L12-91`
* **Function**: `SQLExecutorService.execute_query(raw_sql)` calls `sanitize_and_validate_sql(raw_sql)`, connects to the database engine via `engine.connect()`, executes the query via `connection.execute(text(validated_sql))`, measures latency using `time.perf_counter()`, serializes `Decimal` and `datetime` types into JSON-compatible values, and calculates `row_count`.

### Step 6: Heuristic Visualization Recommender
* **Location**: `backend/app/services/executor_service.py:L93-132`
* **Function**: `_recommend_visualization(columns, rows)` inspects column data types in the first row. It assigns the first string column as `x_axis` and numeric columns as `y_axis`. If single numeric column and `<= 7` rows, recommends `"pie"`; if date/year/month substring in `x_axis`, recommends `"line"`; if numeric columns present, recommends `"bar"`; otherwise falls back to `"table"`.

### Step 7: Query Audit Storage
* **Location**: `backend/app/api/endpoints.py:L25-45, L159-165, L200-206`
* **Function**: `_db_insert_history(prompt, sql_query, row_count, execution_time_ms, status)` executes an `INSERT INTO query_history` query capturing prompt text, generated SQL, row count, execution latency, and status (`"success"`, `"blocked"`, or `"error"`).

### Step 8: Multi-Format Data Export
* **Location**: `backend/app/services/export_service.py:L6-76`
* **Function**: Handled by endpoint `POST /api/export` (`endpoints.py:L229-257`):
  * CSV: `ExportService.export_to_csv()` via `pandas.DataFrame.to_csv()` returning an in-memory `io.BytesIO` stream.
  * Excel: `ExportService.export_to_excel()` via `pandas.ExcelWriter(output, engine='openpyxl')`.
  * PDF: `ExportService.export_to_pdf()` via ReportLab `SimpleDocTemplate`, `Paragraph`, and `Table` styles.

---

## 7. DATABASES & STORAGE

The project supports two relational backends through SQLAlchemy abstraction:

```
                  ┌──────────────────────────────────────────────┐
                  │          SQLAlchemy Engine Abstraction       │
                  │        (backend/app/db/session.py)           │
                  └──────────────────────┬───────────────────────┘
                                         │
                        ┌────────────────┴────────────────┐
                        ▼                                 ▼
             [Primary: PostgreSQL 16]         [Fallback: SQLite Database]
             • postgres:16-alpine container   • backend/text2sql.db file
             • Connection pool: size 10       • Activated if Postgres offline
             • Seeded by database/init.sql    • 12 tables, 384 seed rows
```

### 7.1 Database Engines
1. **Primary**: PostgreSQL 16 via Docker container `text2sql-postgres` (`docker-compose.yml:L3-19`). Connected using URL string `postgresql+psycopg2://postgres:[REDACTED]@localhost:5432/text2sql_db` (`backend/app/core/config.py:L18-19`).
2. **Fallback**: SQLite file `backend/text2sql.db` (`backend/app/db/session.py:L38-39`). Connected when PostgreSQL connection fails in `initialize_engine()` (`session.py:L36-51`).

### 7.2 Tables & Usage
| Table Name | Schema Attributes | Where Read in Code | Where Written in Code |
| :--- | :--- | :--- | :--- |
| `query_history` | `id` (PK), `prompt`, `sql_query`, `row_count`, `execution_time_ms`, `status`, `created_at` | `endpoints.py:L53-56` (`_db_fetch_history()`) | `endpoints.py:L28-42` (`_db_insert_history()`) |
| `departments` | `department_id` (PK), `department_name`, `building`, `budget` | Dynamic generated SQL (`executor_service.py:L39`), `session.py:L114-132` | `database/init.sql:L65-71` |
| `instructors` | `instructor_id` (PK), `name`, `email`, `department_id` (FK), `salary` | Dynamic generated SQL (`executor_service.py:L39`), `session.py:L114-132` | `database/init.sql:L73-79, L223-229` |
| `students` | `student_id` (PK), `first_name`, `last_name`, `email`, `department_id` (FK), `cgpa`, `enrollment_year` | Dynamic generated SQL (`executor_service.py:L39`), `session.py:L114-132` | `database/init.sql:L81-92, L244-335` |
| `courses` | `course_id` (PK), `course_code`, `course_title`, `credits`, `department_id` (FK), `instructor_id` (FK) | Dynamic generated SQL (`executor_service.py:L39`), `session.py:L114-132` | `database/init.sql:L94-100, L231-242` |
| `enrollments` | `enrollment_id` (PK), `student_id` (FK), `course_id` (FK), `grade`, `grade_point`, `semester` | Dynamic generated SQL (`executor_service.py:L39`), `session.py:L114-132` | `database/init.sql:L102-112, L337-520` |
| `customers` | `customer_id` (PK), `customer_name`, `city`, `country`, `created_at` | Dynamic generated SQL (`executor_service.py:L39`), `session.py:L114-132` | `database/init.sql:L151-157, L535-546` |
| `products` | `product_id` (PK), `product_name`, `category`, `unit_price`, `stock_quantity` | Dynamic generated SQL (`executor_service.py:L39`), `session.py:L114-132` | `database/init.sql:L159-165, L522-533` |
| `orders` | `order_id` (PK), `customer_id` (FK), `order_date`, `total_amount`, `status` | Dynamic generated SQL (`executor_service.py:L39`), `session.py:L114-132` | `database/init.sql:L167-173, L548-559` |
| `order_items` | `item_id` (PK), `order_id` (FK), `product_id` (FK), `quantity`, `price_per_unit` | Dynamic generated SQL (`executor_service.py:L39`), `session.py:L114-132` | `database/init.sql:L175-182` |
| `corp_departments`| `dept_id` (PK), `dept_name`, `location` | Dynamic generated SQL (`executor_service.py:L39`), `session.py:L114-132` | `database/init.sql:L203-208` |
| `employees` | `emp_id` (PK), `emp_name`, `job_title`, `dept_id` (FK), `hire_date`, `salary` | Dynamic generated SQL (`executor_service.py:L39`), `session.py:L114-132` | `database/init.sql:L210-217, L561-571` |

*Vector Databases & Embeddings*: **NOT FOUND**. There are no vector databases (such as Chroma, Pinecone, FAISS, Weaviate, or pgvector), no embedding models, and no retrieval-augmented generation (RAG) modules in the repository (`codebase_analysis.md:L75`).

---

## 8. MODELS / ANALYTICS / ML

### 8.1 Machine Learning Implementation
* **Local ML Code**: **NOT FOUND**. There is no PyTorch, TensorFlow, Hugging Face Transformers, or ONNX code in the application backend (`backend/requirements.txt`).
* **Training Code**: **NOT FOUND**. No training, fine-tuning, or parameter optimization scripts exist in the repository.
* **Weights & Hyperparameters**: **NOT FOUND**. No model weight checkpoints exist in the repository.
* **Inference Mechanism**: Remote API call to Google Gemini via HTTPS (`backend/app/services/ai_service.py:L140-143`).
  * API Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}`
  * Configured Model: `gemini-3.6-flash` (`backend/app/core/config.py:L23`)
  * Runtime Fallback Models: `gemini-flash-lite-latest`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3.6-flash`, `gemini-flash-latest` (`backend/app/services/ai_service.py:L128-134`)
  * Generation Config: `temperature: 0.0`, `maxOutputTokens: 2048` (`backend/app/services/ai_service.py:L122-125`)

### 8.2 Actual Evaluation Metrics Saved in the Repository
All metrics cited from JSON result artifacts in `backend/benchmarks/`:

| Artifact File | Cases | Gen Success Rate | Execution Accuracy (EA) | Column Match Rate | Exact Match Rate | Avg Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `backend/benchmarks/latest_benchmark.json` | 30 | **100.0%** (`1.0`) | **96.7%** (`0.9667`) | **80.0%** (`0.80`) | **36.7%** (`0.3667`) | **2,362 ms** |
| `backend/benchmarks/benchmark_results_20261013_123222.json` | 30 | 96.7% (`0.9667`) | 86.7% (`0.8667`) | 43.3% (`0.4333`) | 3.3% (`0.0333`) | 7,049 ms |
| `backend/benchmarks/benchmark_results_20261013_122803.json` | 30 | 96.7% (`0.9667`) | 80.0% (`0.8000`) | 36.7% (`0.3667`) | 3.3% (`0.0333`) | 3,973 ms |
| `backend/benchmarks/benchmark_results_20261013_122403.json` | 30 | 100.0% (`1.0`) | 56.7% (`0.5667`) | 46.7% (`0.4667`) | 3.3% (`0.0333`) | 6,581 ms |
| `backend/benchmarks/benchmark_results_20261009_100950.json` | 30 | 76.7% (`0.7667`) | 76.7% (`0.7667`) | 26.7% (`0.2667`) | 6.7% (`0.0667`) | 15,544 ms |
| `backend/benchmarks/benchmark_results_20261009_100007.json` | 30 | 0.0% (`0.0`) | 0.0% (`0.0`) | 0.0% (`0.0`) | 0.0% (`0.0`) | 0.7 ms |

*Note on external documentation claims*:
- `REVIEW_II_REPORT.md:L118-121` reports comparative accuracy numbers for `DeepSeek-Coder-33B-Instruct` (96.2%), `HuggingFace SQLCoder-7B` (91.8%), and `CodeT5 / T5-Base` (78.5%). **These models do not exist in the code.** There are no scripts running these models or measuring these numbers in the repository.
- `datasets/model_evaluation_50_test_cases.md:L1-10` reports 50 test cases with 100.0% accuracy and `< 1.5 ms` query latency attributed to `DeepSeek-Coder-33B-Instruct`. Inspection of `scratch/generate_benchmark_50.py:L147` reveals that this string was hardcoded into a markdown generator script that measured local database execution latency, not model inference latency.

---

## 9. BACKEND / API SPECIFICATION

All endpoints defined in `backend/app/api/endpoints.py` and mounted under prefix `/api` (`backend/app/main.py:L22`):

### 1. `GET /api/health`
* **File Location**: `backend/app/api/endpoints.py:L99-116`
* **Inputs**: None
* **Outputs**: `{"status": "online", "database_connected": bool, "ai_model": str, "timestamp": str}`
* **Logic**: Tests database connection by running `SELECT 1;` on the SQLAlchemy engine.

### 2. `GET /api/schema`
* **File Location**: `backend/app/api/endpoints.py:L118-123`
* **Inputs**: None
* **Outputs**: `{"tables": {<table_name>: {"columns": [...], "detailed_columns": [...], "foreign_keys": [...]}}}`
* **Logic**: Calls `inspect_db_schema()` from `app.db.session`.

### 3. `POST /api/generate-sql`
* **File Location**: `backend/app/api/endpoints.py:L125-134`
* **Inputs**: `GenerateSQLRequest` JSON: `{"prompt": str}`
* **Outputs**: `{"is_safe": bool, "blocked": bool, "violation_type": Optional[str], "blocked_operation": Optional[str], "blocked_sql": Optional[str], "generated_sql": str, "suggested_safe_sql": Optional[str], "explanation": str, "security_message": Optional[str]}`
* **Logic**: Calls `ai_service.generate_sql(prompt)`.

### 4. `POST /api/execute-query`
* **File Location**: `backend/app/api/endpoints.py:L136-141`
* **Inputs**: `ExecuteQueryRequest` JSON: `{"sql_query": str}`
* **Outputs**: `{"success": bool, "blocked": bool, "sql_query": str, "columns": list[str], "rows": list[dict], "row_count": int, "execution_time_ms": float, "visualization": dict, "error": Optional[str]}`
* **Logic**: Calls `executor_service.execute_query(sql_query)`.

### 5. `POST /api/query`
* **File Location**: `backend/app/api/endpoints.py:L143-221`
* **Inputs**: `ProcessQueryRequest` JSON: `{"prompt": str}`
* **Outputs**: Combined response containing prompt, safety/blocked status, generated SQL, explanation, and nested `execution` dictionary with columns, rows, latency, and recommended chart config.
* **Logic**: Full pipeline execution: calls `ai_service.generate_sql()`, logs blocked attempts to DB history, executes safe SQL via `executor_service.execute_query()`, logs result to `query_history`, and returns structured payload.

### 6. `GET /api/history`
* **File Location**: `backend/app/api/endpoints.py:L223-227`
* **Inputs**: None
* **Outputs**: `{"history": [{"id": str, "prompt": str, "sql_query": str, "row_count": int, "execution_time_ms": float, "status": str, "timestamp": str}]}`
* **Logic**: Calls `_db_fetch_history()` to read the 50 most recent records from the `query_history` table.

### 7. `POST /api/export`
* **File Location**: `backend/app/api/endpoints.py:L229-258`
* **Inputs**: `ExportRequest` JSON: `{"columns": list[str], "rows": list[dict], "sql_query": Optional[str], "format": "csv" | "excel" | "pdf"}`
* **Outputs**: `StreamingResponse` with appropriate MIME type and `Content-Disposition` attachment filename (`query_results.csv`, `query_results.xlsx`, or `query_results.pdf`).
* **Logic**: Dispatches to `export_service` based on format.

### 8. `GET /api/benchmarks`
* **File Location**: `backend/app/api/endpoints.py:L268-272`
* **Inputs**: None
* **Outputs**: Benchmark report JSON (`run_timestamp`, `total_cases`, `metrics`, `cases`, `is_running`, `live_status`).
* **Logic**: Calls `benchmark_service.get_latest_results()`.

### 9. `GET /api/benchmarks/status`
* **File Location**: `backend/app/api/endpoints.py:L274-278`
* **Inputs**: None
* **Outputs**: Benchmark runner state JSON (`is_running`, `current_index`, `total_cases`, `passed_count`, `failed_count`, etc.).
* **Logic**: Calls `benchmark_service.get_status()`.

### 10. `POST /api/benchmarks/run`
* **File Location**: `backend/app/api/endpoints.py:L280-286`
* **Inputs**: Optional `BenchmarkRunRequest` JSON: `{"domain": Optional[str], "difficulty": Optional[str]}`
* **Outputs**: `{"status": "started" | "already_running", "message": str, "started_at": str}`
* **Logic**: Calls `benchmark_service.trigger_run()`, launching a background worker thread (`_run_suite_worker`).

### 11. `GET /` (Root Route)
* **File Location**: `backend/app/main.py:L24-30`
* **Inputs**: None
* **Outputs**: `{"message": "Welcome to AI-Powered Text-to-SQL System API", "docs": "/docs", "version": "1.0.0"}`

---

## 10. DASHBOARD — PAGE BY PAGE SPECIFICATION

### Page 1: Interactive Workspace (`/`, `frontend/src/app/page.tsx`)
* **Header Badges**:
  1. *Spider EA Badge*: Displays `96.7% Spider EA`, links to `/benchmarks` (`page.tsx:L107-114`).
  2. *AI Engine Badge*: Displays `Google Gemini AI` (`page.tsx:L115-118`).
  3. *Database Badge*: Displays `PostgreSQL Active` (`page.tsx:L119-122`).
* **Widget: PromptInput** (`frontend/src/components/PromptInput.tsx`):
  * Visual: Search input bar with submit button and 5 quick-prompt suggestion pills (`"Show all students with CGPA between 7 to 9"`, `"Show all students with CGPA greater than 8"`, `"Top 5 products by revenue"`, `"Average salary per department"`, `"List low stock products under 50 units"`).
  * Data Source: User text entry. Calls `processTextToSqlQuery()` (`POST /api/query`).
  * What viewer learns: Immediate entrypoint to submit questions in conversational English.
* **Widget: SecurityRestrictionCard** (`frontend/src/components/SecurityRestrictionCard.tsx`):
  * Visual: Red illuminated alert card with animated shield icon, blocked command strikethrough, policy explanation, and interactive button: `"Execute Safe SELECT Alternative"`.
  * Data Source: Rendered when `currentQueryResponse.blocked === true` (`page.tsx:L156-166`).
  * What viewer learns: Visual proof that data modification attacks (DELETE, DROP, UPDATE) are blocked, and learns the non-destructive read-only equivalent.
* **Widget: SqlEditor** (`frontend/src/components/SqlEditor.tsx`):
  * Visual: Dark code container displaying generated SQL with real-time safety badge (`"Validated Safe"` or `"Restricted / Unsafe SQL"`), copy button, execute button, and AI logic explanation box.
  * Data Source: `currentQueryResponse.generated_sql` and `currentQueryResponse.explanation`.
  * What viewer learns: Inspects the synthesized SQL query before or after execution, with the ability to tweak SQL and rerun manually.
* **Widget: ResultsTable** (`frontend/src/components/ResultsTable.tsx`):
  * Visual: Data table with pagination (10 rows/page), column headers in terracotta font, inline text filter, row count indicator, execution latency badge in milliseconds, and export button.
  * Data Source: `currentQueryResponse.execution.rows` and `currentQueryResponse.execution.columns`.
  * What viewer learns: Inspects tabular database records returned by PostgreSQL with execution latency proof.
* **Widget: Visualizer** (`frontend/src/components/Visualizer.tsx`):
  * Visual: Recharts interactive chart container with switchable tabs: **Bar Chart**, **Line Chart**, **Pie Chart**, **Area Chart**, with tooltip hover cards and legend.
  * Data Source: `currentQueryResponse.execution.rows` and `currentQueryResponse.execution.visualization`.
  * What viewer learns: Graphical distribution, trends, or comparisons inferred from query results.
* **Widget: HistorySidebar** (`frontend/src/components/HistorySidebar.tsx`):
  * Visual: Vertical panel displaying up to 50 recent queries with row count, execution latency, blocked badges, and click-to-rerun handler.
  * Data Source: Fetched from `GET /api/history` on mount and after each query submission (`HistorySidebar.tsx:L16-29`).
* **Widget: ExportModal** (`frontend/src/components/ExportModal.tsx`):
  * Visual: Modal dialog providing 3 download options: **CSV (.csv)**, **Excel (.xlsx)**, and **PDF Report (.pdf)**.
  * Data Source: Sends active `columns`, `rows`, and `sql_query` to `POST /api/export` (`ExportModal.tsx:L35-51`).

### Page 2: Accuracy Benchmarks & Records (`/benchmarks`, `frontend/src/app/benchmarks/page.tsx`)
* **Header & Controls**:
  * Visual: "Live Real-Time" badge, "Refresh" button, and "Run Spider Suite" trigger button (`benchmarks/page.tsx:L280-320`).
* **Metric Cards (6 KPIs)**:
  1. *Execution Accuracy (EA)*: `96.7%` (`benchmarks/page.tsx:L229`)
  2. *Generation Success Rate*: `100.0%` (`benchmarks/page.tsx:L230`)
  3. *Column Match Rate (CM)*: `80.0%` (`benchmarks/page.tsx:L231`)
  4. *Exact Match Rate (EM)*: `36.7%` (`benchmarks/page.tsx:L232`)
  5. *Average Latency*: `2,362 ms` (`benchmarks/page.tsx:L233`)
  6. *Blocked by Guardrails*: `0` (`benchmarks/page.tsx:L234`)
* **Filter Bars**:
  * Domain tabs: `All` (30), `University` (12), `E-Commerce` (9), `Corporate` (9), `Cross-Domain` (`benchmarks/page.tsx:L244-252`).
  * Difficulty tabs: `All`, `easy`, `medium`, `hard`.
  * Status tabs: `All`, `Passed`, `Failed`.
  * Search input: Text filter matching prompt or SQL query.
* **Accordion Test Case Cards (30 Cases)**:
  * Visual: Expandable case cards displaying ID, domain, difficulty, natural language prompt, gold SQL, generated SQL, latency in ms, status badges (EA, CM, EM), and an embedded `CaseRecordsTable` (`benchmarks/page.tsx:L17-143`).
  * `CaseRecordsTable`: Interactive data grid displaying up to 50 live records returned from PostgreSQL for each benchmark test case, with search filter, pagination (8 rows/page), and `"Open in Workspace"` deep link.

### Page 3: Query Execution History (`/history`, `frontend/src/app/history/page.tsx`)
* **Visual**: Audit trail list rendering all recorded queries from `query_history` table (`history/page.tsx:L48-105`).
* **Cards**: Each entry renders user prompt, status badge (`BLOCKED` or success), row count, execution time ms, formatted SQL code box, logging timestamp, and `"Open in Workbench"` navigation link.
* **Data Source**: Fetched via `fetchQueryHistory()` (`GET /api/history`).

### Page 4: Database Schema Explorer (`/settings`, `frontend/src/app/settings/page.tsx`)
* **Metric Cards**: Total Tables (`11`), Total Columns (`60`), Foreign Keys (`11`), Engine Status (`Connected`).
* **Domain Tabs**: All Tables (`11`), Academic (`5`), E-Commerce (`4`), Corporate (`2`).
* **Search Box**: Real-time filtering across table names and attribute column names (`settings/page.tsx:L232-250`).
* **Table Entity Cards (11 Cards)**:
  * Displays table name, domain badge, column count, FK count, copy button.
  * Columns list with data type badges (`INTEGER`, `VARCHAR`, `REAL`, `DATE`, `TIMESTAMP`) and primary key (`PK`) chips.
  * Foreign key section displaying arrows: `<column> -> <referred_table> (<referred_column>)`.
  * `"Query in Workbench"` link.
* **Data Source**: `fetchDatabaseSchema()` (`GET /api/schema`).

### Page 5: About & Architecture (`/about`, `frontend/src/app/about/page.tsx`)
* **Header**: Health status badge, ping latency measurement (`performance.now()`), and active model name fetched from `GET /api/health` (`about/page.tsx:L18-35`).
* **Pipeline Stages (5 Cards)**:
  1. *Prompt Contextualization* (Terminal icon)
  2. *Gemini LLM Inference* (Cpu icon)
  3. *AST Security Guardrails* (ShieldCheck icon)
  4. *PostgreSQL Execution* (Database icon)
  5. *Analytics & Multi-Export* (Download icon)
* **Tech Stack Breakdown**: Structured cards detailing Frontend, Backend, Security, and Storage layers.

---

## 11. END-TO-END DATA LINEAGE

Trace for each dashboard visual element:

### Lineage 1: ResultsTable
$$\text{PostgreSQL Table records} \xrightarrow[\text{session.py:initialize\_engine()}]{\text{Raw storage}} \text{Database} \xrightarrow[\text{executor\_service.py:execute\_query()}]{\text{SQLAlchemy connection.execute()}} \text{Python rows list[dict]} \xrightarrow[\text{endpoints.py:/query}]{\text{JSON API response}} \text{ResultsTable.tsx:paginatedRows}$$

### Lineage 2: Visualizer (Recharts Charts)
$$\text{Database rows} \xrightarrow[\text{executor\_service.py:\_recommend\_visualization()}]{\text{Detect numeric/string columns}} \text{Recommended chart type + axes} \xrightarrow[\text{api.ts:processTextToSqlQuery()}]{\text{API JSON payload}} \text{Visualizer.tsx:ResponsiveContainer} \xrightarrow[\text{Recharts}]{\text{Bar/Line/Pie/Area SVG}}$$

### Lineage 3: HistorySidebar & History Page
$$\text{User prompt + executed SQL} \xrightarrow[\text{endpoints.py:\_db\_insert\_history()}]{\text{INSERT INTO query\_history}} \text{query\_history table} \xrightarrow[\text{endpoints.py:\_db\_fetch\_history()}]{\text{SELECT ... LIMIT 50}} \text{GET /api/history} \xrightarrow[\text{api.ts:fetchQueryHistory()}]{\text{JSON}} \text{HistorySidebar.tsx \& history/page.tsx}$$

### Lineage 4: Benchmarks Accordions & CaseRecordsTable
$$\text{benchmark\_suite.json} \xrightarrow[\text{benchmark\_service.py:\_run\_suite\_worker()}]{\text{Internal execution}} \text{latest\_benchmark.json} \xrightarrow[\text{endpoints.py:GET /benchmarks}]{\text{JSON response}} \text{benchmarks/page.tsx} \xrightarrow[\text{c.records}]{\text{CaseRecordsTable paginated table}}$$

### Lineage 5: Schema Explorer Entity Cards
$$\text{PostgreSQL DDL catalog} \xrightarrow[\text{session.py:inspect\_db\_schema()}]{\text{SQLAlchemy inspect() reflection}} \text{In-memory \_schema\_cache} \xrightarrow[\text{endpoints.py:GET /schema}]{\text{JSON payload}} \text{settings/page.tsx:filteredTables}$$

### Lineage 6: Export Downloads (CSV, Excel, PDF)
$$\text{ResultsTable rows} \xrightarrow[\text{ExportModal.tsx:handleExport()}]{\text{POST /api/export}} \text{export\_service.py} \xrightarrow[\text{pandas / openpyxl / reportlab}]{\text{io.BytesIO byte stream}} \text{Browser download blob (URL.createObjectURL)}$$

---

## 12. HOW TO RUN THE PROJECT

### 12.1 Environment Variables
All variable names cited from `.env.example` and `backend/app/core/config.py`:
* `POSTGRES_USER` — Username for PostgreSQL (default: `postgres`)
* `POSTGRES_PASSWORD` — Password for PostgreSQL (`[REDACTED]`)
* `POSTGRES_SERVER` — Hostname of database server (default: `localhost` for local, `postgres` for Docker)
* `POSTGRES_PORT` — Port number for database (default: `5432`)
* `POSTGRES_DB` — Database name (default: `text2sql_db`)
* `GEMINI_API_KEY` — Google Gemini API key (`[REDACTED]`)
* `GEMINI_MODEL` — Target Gemini model identifier (default: `gemini-3.6-flash`, `.env.example:L10` lists `gemini-1.5-flash`)
* `NEXT_PUBLIC_API_URL` — Backend API base URL for frontend (default: `http://localhost:8000/api`)

### 12.2 Execution via Docker Compose (Documented in `README.md:L87-108`)
```bash
# 1. Prepare environment configuration
cp .env.example .env
# Edit .env and supply GEMINI_API_KEY=[REDACTED]

# 2. Build and launch all services
docker compose up --build
```
* Frontend accessible at: `http://localhost:3000`
* Backend Swagger Docs at: `http://localhost:8000/docs`
* PostgreSQL at: `localhost:5432`

### 12.3 Execution for Local Development (Documented in `README.md:L110-147`)
```bash
# 1. Backend Setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run Unit Tests
PYTHONPATH=. pytest tests/test_sql_validator.py

# Launch Backend Server
uvicorn app.main:app --reload --port 8000

# 2. Frontend Setup (in separate terminal)
cd frontend
npm install
npm run dev
```

---

## 13. TESTS & VALIDATION

### 13.1 Unit Test Suite (`backend/tests/test_sql_validator.py`)
Run command: `PYTHONPATH=backend pytest backend/tests/test_sql_validator.py`  
Result: **7 passed in 0.01s** (Verified via read-only shell execution)

The test file contains 7 test cases:
1. `test_valid_select_query` (`test_sql_validator.py:L4-8`): Confirms `SELECT student_id, first_name, cgpa FROM students WHERE cgpa > 8.0;` passes validation and returns normalized SQL ending with `;`.
2. `test_valid_with_cte_query` (`test_sql_validator.py:L10-14`): Confirms `WITH top_students AS (...) SELECT * FROM top_students;` passes validation and preserves `WITH` prefix.
3. `test_reject_drop_table` (`test_sql_validator.py:L15-19`): Confirms `DROP TABLE students;` raises `SQLValidationError` containing `"Forbidden"`.
4. `test_reject_delete_from` (`test_sql_validator.py:L21-25`): Confirms `DELETE FROM students WHERE student_id = 1;` raises `SQLValidationError` containing `"Forbidden"`.
5. `test_reject_update` (`test_sql_validator.py:L27-31`): Confirms `UPDATE students SET cgpa = 10.0 WHERE student_id = 1;` raises `SQLValidationError` containing `"Forbidden"`.
6. `test_reject_multiple_statements` (`test_sql_validator.py:L33-38`): Confirms `SELECT * FROM students; DROP TABLE courses;` raises `SQLValidationError` blocking multi-statement injection.
7. `test_reject_truncate` (`test_sql_validator.py:L39-44`): Confirms `TRUNCATE TABLE enrollments;` raises `SQLValidationError` containing `"Forbidden"`.

### 13.2 Accuracy Benchmark Suite (`backend/benchmarks/run_benchmark.py`)
Runs 30 test cases from `benchmark_suite.json` comparing generated SQL results with gold standard SQL executed directly on the database engine.
Calculates 4 metrics:
* Generation Success Rate
* Execution Accuracy (EA)
* Column Match Rate (CM)
* Exact Match Rate (EM)

### 13.3 Yale Spider Evaluation Script (`backend/benchmarks/spider_eval.py`)
CLI evaluator implementing Yale Spider benchmark Exact Set Match (clause-by-clause structural comparison of SELECT, FROM, WHERE, GROUP BY, HAVING, ORDER BY) and Execution Accuracy against Spider SQLite databases or project schema.

### 13.4 Dataset Integrity Script (`datasets/loader.py`)
Run command: `python3 datasets/loader.py`  
Result: Verified 1,034 validation questions, 8,659 total training questions, 166 SQLite databases, and project seed DB with 12 tables and 384 rows.

---

## 14. KNOWN GAPS, DISCREPANCIES & HARDCODED VALUES

### 14.1 Discrepancies Between Documentation and Actual Code
1. **Hugging Face Transformers / Local Model Claim**:
   * *Claim*: `README.md:L9, L15` states: `"AI: HuggingFace Transformers (SQLCoder / T5)"`.
   * *Fact*: `backend/requirements.txt` does not include `transformers`, `torch`, or `accelerate`. `backend/app/services/ai_service.py:L22-26` connects exclusively to the Google Gemini cloud API via HTTPS.
2. **DeepSeek-Coder and SQLCoder Benchmarking Claims**:
   * *Claim*: `REVIEW_II_REPORT.md:L118-121` reports comparative Spider benchmark accuracy numbers for `DeepSeek-Coder-33B-Instruct` (96.2%), `HuggingFace SQLCoder-7B` (91.8%), and `CodeT5 / T5-Base` (78.5%).
   * *Fact*: No code exists in the repository that runs or evaluates DeepSeek-Coder, SQLCoder, or CodeT5.
3. **Next.js Version Discrepancy**:
   * *Claim*: `README.md:L6, L60` and `frontend/src/app/about/page.tsx:L86` state: `"Next.js 15"`.
   * *Fact*: `frontend/package.json:L15` specifies `"next": "16.2.11"` and `"react": "19.2.4"`.
4. **Benchmark Suite Count Discrepancy**:
   * *Claim*: `REVIEW_II_REPORT.md:L149-202` and `datasets/model_evaluation_50_test_cases.md:L5` report a "50 Test Cases Benchmark Evaluation Matrix".
   * *Fact*: The actual benchmark suite in `backend/benchmarks/benchmark_suite.json:L1-200` contains exactly 30 test cases. The 50-test-case report was generated by `scratch/generate_benchmark_50.py`.
5. **Spider Dataset Origin Claim**:
   * *Claim*: `README.md:L17` refers to schemas inspired by the Yale Spider Benchmark across `"University, E-Commerce, Corporate domains"`.
   * *Fact*: In the Spider dataset (`datasets/spider/tables.json`), University domains (`college_2`, `activity_1`, etc.) exist, but the Corporate HR schema (`corp_departments`, `employees`) is a custom schema added to this project.

### 14.2 Hardcoded Values in Code
1. **Hardcoded Fallback DDL Schema**:
   * *Location*: `backend/app/db/session.py:L146-158`
   * *Description*: If database inspection returns an empty dictionary, a hardcoded 11-table DDL string is returned as fallback.
2. **Hardcoded Destructive Entity Names**:
   * *Location*: `backend/app/services/ai_service.py:L66-70`
   * *Description*: Table list `["students", "orders", "products", "customers", "employees", "courses", "departments", "instructors", "order_items", "enrollments", "corp_departments"]` is hardcoded for fallback inspection query generation, with a final fallback of `"SELECT * FROM students LIMIT 10;"`.
3. **Hardcoded Few-Shot Schema Guidelines**:
   * *Location*: `backend/app/services/ai_service.py:L99-110`
   * *Description*: Example SQL queries for University, Corporate, and E-Commerce queries are hardcoded directly into the system prompt.
4. **Hardcoded Accuracy Pill in Frontend**:
   * *Location*: `frontend/src/app/page.tsx:L113`
   * *Description*: The header renders a static link badge reading `"96.7% Spider EA"`.
5. **Hardcoded Default Database Credentials**:
   * *Location*: `docker-compose.yml:L9, L34`, `backend/app/core/config.py:L12`
   * *Description*: Default password `postgrespassword` is hardcoded as fallback in config and docker compose.

### 14.3 Dead Code & Unused Files
1. `scratch/generate_benchmark_50.py`: Standalone scratch script not imported by any module in `app/`.
2. `generate_review2_doc.py`: Standalone Word document generator not imported by the web application.
3. `datasets/spider.zip`: Compressed zip archive (95 MB) remaining in workspace after extraction into `datasets/spider/`.
4. `datasets/huggingface_spider/train.json` & `train.parquet`: Training datasets (7,000 examples) present in repo but not consumed by the runtime application (which only queries remote Gemini API).

---

## 15. FACULTY Q&A PREPARATION (15 QUESTIONS)

### Q1: "What AI model does your system use, and how is it hosted?"
* **Answer**: The system uses the Google Gemini cloud API via HTTPS (`backend/app/services/ai_service.py:L140-143`). The default configured model is `gemini-3.6-flash` (`backend/app/core/config.py:L23`), with automated runtime fallbacks to `gemini-flash-lite-latest`, `gemini-3.5-flash-lite`, and `gemini-flash-latest` (`backend/app/services/ai_service.py:L128-134`). The model is not hosted locally; no GPU or local model weights are used.

### Q2: "Why does the README mention Hugging Face Transformers (`SQLCoder` / `T5`) while the code uses Gemini?"
* **Answer**: The `README.md:L9, L15` contains an outdated architectural plan or aspiration. Examination of `backend/requirements.txt` reveals that `torch` and `transformers` are absent. The actual implementation in `backend/app/services/ai_service.py` is entirely written using the Google Gemini REST API.

### Q3: "How does the system prevent hallucinating table and column names?"
* **Answer**: The system uses real-time schema grounding. `backend/app/db/session.py:L108-136` uses SQLAlchemy's `inspect(engine)` to reflect live table names, column data types, and foreign keys. This schema is formatted into DDL statements by `format_schema_for_prompt()` (`session.py:L142-164`) and injected into the Gemini system prompt (`backend/app/services/ai_service.py:L98`) on every request.

### Q4: "How do you guarantee that a user cannot drop or delete database records?"
* **Answer**: Through a dual-layer security mechanism:
  1. *Prompt & Regex Interceptor*: `backend/app/services/ai_service.py:L197-230` flags destructive keywords (`DELETE`, `DROP`, `UPDATE`, `TRUNCATE`, `ALTER`) in both the prompt and LLM output, blocking execution and converting the statement into a safe read-only preview `SELECT`.
  2. *AST Parser*: `backend/app/services/sql_validator.py:L14-66` uses `sqlparse` to construct an Abstract Syntax Tree. It asserts that queries must begin with `SELECT` or `WITH`, rejects queries with multiple statements (blocking semicolon injection), and scans all AST tokens against `FORBIDDEN_KEYWORDS`. Destructive queries raise `SQLValidationError` before reaching the database driver (`backend/app/services/executor_service.py:L23-35`).

### Q5: "What happens if a user submits a multi-statement injection attack like `SELECT * FROM students; DROP TABLE courses;`?"
* **Answer**: The AST parser in `backend/app/services/sql_validator.py:L32-38` parses the query into individual statements using `sqlparse.parse()`. If more than one non-empty statement is detected, it raises `SQLValidationError("Security Warning: Multiple SQL statements are not allowed.")`. This is verified by unit test `test_reject_multiple_statements` in `backend/tests/test_sql_validator.py:L33-38`.

### Q6: "What database does the application use, and what happens if PostgreSQL goes down?"
* **Answer**: The primary database is PostgreSQL 16 running in a Docker container (`docker-compose.yml:L3-19`). In `backend/app/db/session.py:L20-51`, `initialize_engine()` catches connection exceptions. If PostgreSQL is unreachable, it logs a warning and initializes a local SQLite database at `backend/text2sql.db`, automatically converting and seeding DDL from `database/init.sql` (`session.py:L54-83`).

### Q7: "How many tables and records exist in your database?"
* **Answer**: There are 12 tables (`database/init.sql:L7-201`): `departments` (5 rows), `instructors` (10 rows), `students` (100 rows), `courses` (15 rows), `enrollments` (184 rows), `customers` (15 rows), `products` (15 rows), `orders` (15 rows), `order_items` (6 rows), `corp_departments` (4 rows), `employees` (15 rows), and `query_history` (audit log table). Total static seed count is 384 rows, verified in `backend/text2sql.db`.

### Q8: "How does the system decide which chart type to render for a query result?"
* **Answer**: Heuristic type inference is performed by `_recommend_visualization()` in `backend/app/services/executor_service.py:L93-132`. It samples the first row of returned data, classifying columns into numeric and string types. If a single numeric column is returned with `<= 7` rows, it recommends a `pie` chart; if temporal words (`date`, `year`, `month`) appear in the X-axis column, it recommends a `line` chart; if any numeric columns exist, it recommends a `bar` chart; otherwise it returns `"table"`.

### Q9: "What accuracy metrics did you actually achieve, and how were they measured?"
* **Answer**: Based on saved benchmark run `backend/benchmarks/latest_benchmark.json:L4-11` across the 30-case test suite (`benchmark_suite.json`), the system achieved:
  * Generation Success Rate: **100.0%**
  * Execution Accuracy (EA): **96.7%** (29 of 30 cases returned identical rows to gold SQL)
  * Column Match Rate (CM): **80.0%**
  * Exact Match Rate (EM): **36.7%**
  * Average Latency: **2,362 ms** (including Gemini API round-trip)

### Q10: "Why is Exact Match (36.7%) so much lower than Execution Accuracy (96.7%)?"
* **Answer**: Exact Match compares the normalized SQL text string directly against the gold SQL (`run_benchmark.py:L314`). An LLM often generates equivalent SQL using different table aliases (`students AS s` vs `students`), explicit column lists vs `SELECT *`, or alternate `JOIN` order. Execution Accuracy compares the actual row sets returned by the database engine (`run_benchmark.py:L91-163`), confirming semantic equivalence even when query syntax differs.

### Q11: "Does your system use RAG (Retrieval-Augmented Generation) or Vector Databases?"
* **Answer**: No. There is no vector database, no embedding generation, and no chunk retrieval in the repository (`codebase_analysis.md:L75`). The database schema contains 11 domain tables, which formats into roughly 1,200 characters of DDL text. This fits completely within the context window of modern LLMs (e.g. Gemini's 1M-token window), eliminating the need for vector retrieval and avoiding retrieval loss.

### Q12: "How is query execution history logged and displayed?"
* **Answer**: Every query processed by `POST /api/query` is logged by `_db_insert_history()` (`backend/app/api/endpoints.py:L25-45`) into the `query_history` table in PostgreSQL or SQLite. It stores the prompt, generated SQL, row count, execution latency, status (`success` or `blocked`), and timestamp. The frontend fetches this via `GET /api/history` and displays it in `HistorySidebar.tsx` and the dedicated `/history` page (`frontend/src/app/history/page.tsx`).

### Q13: "What file formats can query results be exported into, and how are they generated?"
* **Answer**: Three formats are supported via `POST /api/export` (`backend/app/services/export_service.py:L6-76`):
  1. CSV (`export_to_csv`): Uses `pandas.DataFrame.to_csv()` streaming UTF-8 bytes.
  2. Excel (`export_to_excel`): Uses `pandas.ExcelWriter` with the `openpyxl` engine.
  3. PDF (`export_to_pdf`): Uses ReportLab `SimpleDocTemplate`, rendering the executed SQL query in a highlighted code box and results in a styled `Table`.

### Q14: "What unit tests exist in your codebase?"
* **Answer**: There are 7 unit tests located in `backend/tests/test_sql_validator.py:L1-44`. They test the AST security validator using `pytest`, verifying that valid `SELECT` and `WITH` CTE queries are approved, while destructive operations (`DROP TABLE`, `DELETE FROM`, `UPDATE`, `TRUNCATE`) and multi-statement injection attacks are rejected with a `SQLValidationError`. All 7 tests pass in 0.01s.

### Q15: "What are the primary technical limitations of your current implementation?"
* **Answer**: Verified from code inspection:
  1. *External API Dependency*: Requires internet access and a valid Google Gemini API key; failure or rate limits (HTTP 429) result in service degradation (`backend/app/services/ai_service.py:L162-174`).
  2. *Dialect Limitation*: Schema reflection and queries are tailored to PostgreSQL/SQLite; no multi-dialect translation engine (e.g. Oracle, Snowflake) is implemented.
  3. *Static Heuristic Visualizer*: The chart recommender (`executor_service.py:L93-132`) relies on basic rule-based checks (presence of numbers or date keywords) rather than semantic intent analysis.
  4. *Authentication & Authorization*: There is no user authentication, session management, or role-based access control (RBAC); all users share a single read-only role.

---

## 16. EVIDENCE INDEX

### 16.1 Files Inspected
1. `README.md` (Lines 1–177)
2. `REVIEW_II_REPORT.md` (Lines 1–244)
3. `codebase_analysis.md` (Lines 1–139)
4. `.env.example` (Lines 1–14)
5. `docker-compose.yml` (Lines 1–60)
6. `pyrightconfig.json` (Lines 1–12)
7. `generate_review2_doc.py` (Lines 1–60)
8. `scratch/generate_benchmark_50.py` (Lines 1–208)
9. `docker/backend.Dockerfile` (Lines 1–22)
10. `docker/frontend.Dockerfile` (Lines 1–30)
11. `database/init.sql` (Lines 1–572)
12. `backend/requirements.txt` (Lines 1–15)
13. `backend/app/main.py` (Lines 1–35)
14. `backend/app/core/config.py` (Lines 1–33)
15. `backend/app/db/session.py` (Lines 1–165)
16. `backend/app/api/endpoints.py` (Lines 1–287)
17. `backend/app/services/ai_service.py` (Lines 1–258)
18. `backend/app/services/sql_validator.py` (Lines 1–67)
19. `backend/app/services/executor_service.py` (Lines 1–135)
20. `backend/app/services/export_service.py` (Lines 1–79)
21. `backend/app/services/benchmark_service.py` (Lines 1–330)
22. `backend/benchmarks/benchmark_suite.json` (Lines 1–200)
23. `backend/benchmarks/latest_benchmark.json` (Lines 1–50)
24. `backend/benchmarks/run_benchmark.py` (Lines 1–506)
25. `backend/benchmarks/spider_eval.py` (Lines 1–648)
26. `backend/benchmarks/README.md` (Lines 1–80)
27. `backend/benchmarks/benchmark_results_20261009_100007.json`
28. `backend/benchmarks/benchmark_results_20261009_100950.json`
29. `backend/benchmarks/benchmark_results_20261013_122403.json`
30. `backend/benchmarks/benchmark_results_20261013_122803.json`
31. `backend/benchmarks/benchmark_results_20261013_123222.json`
32. `backend/tests/test_sql_validator.py` (Lines 1–44)
33. `datasets/loader.py` (Lines 1–230)
34. `datasets/populate_full_dataset.py` (Lines 1–369)
35. `datasets/model_evaluation_50_test_cases.md` (Lines 1–94)
36. `datasets/spider/README.txt` (Lines 1–60)
37. `datasets/huggingface_spider/README.md` (Lines 1–50)
38. `frontend/package.json` (Lines 1–32)
39. `frontend/src/services/api.ts` (Lines 1–142)
40. `frontend/src/app/page.tsx` (Lines 1–247)
41. `frontend/src/app/benchmarks/page.tsx` (Lines 1–320)
42. `frontend/src/app/history/page.tsx` (Lines 1–100)
43. `frontend/src/app/settings/page.tsx` (Lines 1–416)
44. `frontend/src/app/about/page.tsx` (Lines 1–100)
45. `frontend/src/components/Navbar.tsx` (Lines 1–106)
46. `frontend/src/components/PromptInput.tsx` (Lines 1–102)
47. `frontend/src/components/SqlEditor.tsx` (Lines 1–142)
48. `frontend/src/components/ResultsTable.tsx` (Lines 1–152)
49. `frontend/src/components/Visualizer.tsx` (Lines 1–177)
50. `frontend/src/components/HistorySidebar.tsx` (Lines 1–98)
51. `frontend/src/components/ExportModal.tsx` (Lines 1–201)
52. `frontend/src/components/SecurityRestrictionCard.tsx` (Lines 1–171)

### 16.2 Read-Only Shell Commands Executed
1. `find . -maxdepth 3 -not -path '*/.*' -not -path './frontend/node_modules*' -not -path './backend/venv*' -not -path '*/__pycache__*'` (Tree exploration)
2. `find . -not -path '*/.*' -not -path './frontend/node_modules*' -not -path './backend/venv*' -not -path '*/__pycache__*' -type f` (Complete file inventory)
3. `find ./frontend/src -type f` (Frontend source code listing)
4. `find ./backend/app -type f` (Backend source code listing)
5. `python3 -c "import sqlite3; conn = sqlite3.connect('backend/text2sql.db'); ..."` (Database table and row count audit)
6. `python3 -c "import sqlite3; ... PRAGMA table_info ..."` (Table schemas, data types, and sample rows)
7. `python3 -c "import os, json; ..."` (HuggingFace Spider dataset inspection)
8. `python3 datasets/loader.py` (Dataset loader CLI run and Spider verification)
9. `python3 -c "import glob, json; ..."` (Audit of benchmark result files in `backend/benchmarks/`)
10. `PYTHONPATH=backend pytest backend/tests/test_sql_validator.py` (Test suite verification: 7 passed)
11. `ls -la .env*` (Environment file inspection)
12. `ls -lh datasets/spider.zip datasets/spider/` (Dataset size and volume check)
13. `python3 -c "import json; ... analyze_json_file ..."` (Data sampling of Spider dev.json, tables.json, and HF validation.json)

---

## 17. SELF-CHECK & UNVERIFIED CLAIMS

In accordance with strict audit rules, the following claims made in repository documentation could **not be verified** or are **refuted by code evidence**:

1. **Hugging Face Transformers (`SQLCoder` / `T5`)**:
   * *Status*: **REFUTED**. `backend/requirements.txt` lacks `transformers` and `torch`. `backend/app/services/ai_service.py` exclusively calls the Google Gemini cloud API.
2. **DeepSeek-Coder-33B, SQLCoder-7B, and CodeT5 Benchmark Metrics**:
   * *Status*: **UNVERIFIED / NOT FOUND IN CODE**. The comparative accuracy table in `REVIEW_II_REPORT.md:L116-122` cannot be reproduced because the code to run or evaluate these models is absent.
3. **Local Fine-Tuning / Training Pipeline**:
   * *Status*: **NOT FOUND**. No training loss curves, training scripts, or weight files exist in the repository.
4. **PostgreSQL Execution Plan Analysis (`EXPLAIN ANALYZE`)**:
   * *Status*: **NOT FOUND IN CODE**. Claimed in `REVIEW_II_REPORT.md:L240` as a future Review III roadmap deliverable; no indexing advisor or execution plan visualizer exists in the active code.
5. **Next.js 15 Claim**:
   * *Status*: **REFUTED**. The frontend dependency in `frontend/package.json:L15` is Next.js `16.2.11` on React `19.2.4`.
6. **50-Case Benchmark Suite in Production**:
   * *Status*: **REFUTED AS RUNTIME SUITE**. The active benchmark suite in `backend/benchmarks/benchmark_suite.json` contains 30 test cases, not 50. The 50-test-case report was generated by an unlinked script in `scratch/generate_benchmark_50.py`.
