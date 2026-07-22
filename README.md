# AI-Powered Text-to-SQL Semantic Query System

An M.Tech level, production-quality full-stack web application that translates natural English questions into valid SQL queries, enforces strict security validation, executes queries on a PostgreSQL database, and visualizes results with interactive tables, charts, execution metrics, and data exports.

![Project Status](https://img.shields.io/badge/Status-Production%20Ready-emerald)
![Next.js](https://img.shields.io/badge/Frontend-Next.js%2015-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-teal)
![Database](https://img.shields.io/badge/Database-PostgreSQL%2016-indigo)
![AI](https://img.shields.io/badge/AI-HuggingFace%20Transformers-orange)

---

## 🌟 Key Features

* **Natural Language Query Engine**: Converts user English prompts into SQL using Hugging Face Transformers (`SQLCoder` / `T5`) and schema-aware semantic translation.
* **SQL Safety & Security Layer**: AST-based parser that blocks destructive statements (`DROP`, `DELETE`, `UPDATE`, `ALTER`, `TRUNCATE`) and multi-statement SQL injection attacks. Only safe, read-only `SELECT` queries are permitted.
* **PostgreSQL Integration**: Pre-populated with relational database schemas inspired by the Yale Spider Benchmark (University, E-Commerce, Corporate domains).
* **Interactive Dashboard**: Sleek dark mode UI built with Next.js 15, Tailwind CSS, and glassmorphism design.
* **Automated Data Visualization**: Dynamic Recharts visualizer rendering Bar, Line, Pie, and Area charts auto-detected based on query column types.
* **Data Export**: Export query results directly to **CSV**, **Excel (.xlsx)**, or **PDF** format.
* **Query History & Audit Log**: Keeps a log of previous prompts, generated SQL, execution latency, and row counts with click-to-rerun capabilities.
* **Live DB Schema Inspector**: Real-time view of database tables, column definitions, and foreign keys.

---

## 🛠️ Architecture & Workflow

```
User (Natural Language Prompt)
         │
         ▼
Next.js 15 Dashboard (React / Tailwind / Recharts)
         │
         ▼
FastAPI REST API Server
         │
 ┌───────┴────────────────────────┐
 │                                │
 ▼                                ▼
AI Text-to-SQL Engine       SQL Safety Validator
(Schema-aware HF Model)     (Enforces SELECT-only)
 │                                │
 └───────┬────────────────────────┘
         ▼
PostgreSQL Database (Docker Container)
         │
         ▼
Result Sets + Latency Metrics + Chart Recommendation
         │
         ▼
Interactive Data Table + Recharts Visualization
```

---

## 📁 Repository Structure

```
Text To SQL/
├── frontend/                 # Next.js 15 + React + Tailwind CSS + Recharts + Axios
│   ├── src/
│   │   ├── app/              # App router pages (Dashboard, History, Settings, About)
│   │   ├── components/       # UI components (Navbar, PromptInput, SqlEditor, ResultsTable, etc.)
│   │   └── services/         # API client & export utilities
│   ├── package.json
│   └── next.config.ts
├── backend/                  # FastAPI + SQLAlchemy + Pydantic + HF Transformers
│   ├── app/
│   │   ├── api/              # REST API Endpoints (/query, /generate-sql, /execute-query, /export)
│   │   ├── core/             # Environment & configuration settings
│   │   ├── db/               # SQLAlchemy session & schema reflection
│   │   └── services/         # AI generator, SQL validator, executor & export service
│   ├── tests/                # Pytest unit & safety validation test suite
│   └── requirements.txt
├── database/                 # PostgreSQL initialization & Spider dataset seeds
│   └── init.sql
├── docker/                   # Custom Dockerfiles
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
├── docker-compose.yml        # Multi-container orchestration (postgres, backend, frontend)
├── README.md
└── .env.example
```

---

## 🚀 Quickstart with Docker Compose

Ensure **Docker** and **Docker Compose** are installed on your machine.

### 1. Clone & Setup Environment

```bash
cp .env.example .env
```

### 2. Build and Run Container Services

```bash
docker compose up --build
```

Access the services:
* **Frontend Dashboard**: `http://localhost:3000`
* **FastAPI Backend Swagger Docs**: `http://localhost:8000/docs`
* **PostgreSQL Database**: `localhost:5432` (`db: text2sql_db`, `user: postgres`, `pass: postgrespassword`)

---

## 💻 Local Development Setup (Without Docker)

### Prerequisites
* **Node.js**: v20+ or v26+
* **Python**: v3.11+
* **PostgreSQL**: Running instance or Docker PostgreSQL

### 1. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run Pytest suite:

```bash
PYTHONPATH=. pytest tests/test_sql_validator.py
```

Start backend API server:

```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your web browser.

---

## 🔗 REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `POST /api/query` | `POST` | Combined endpoint: NL Prompt → SQL → Security Check → Execution → Visualizer Metadata |
| `POST /api/generate-sql` | `POST` | Translates natural language prompt into SQL query + explanation |
| `POST /api/execute-query` | `POST` | Validates safety and executes raw or custom SQL query on PostgreSQL |
| `GET /api/schema` | `GET` | Fetches live database schema (tables, columns, types, foreign keys) |
| `GET /api/history` | `GET` | Retrieves recent query execution history log |
| `POST /api/export` | `POST` | Generates downloadable CSV, Excel (`.xlsx`), or PDF document |
| `GET /api/health` | `GET` | Health check endpoint for database connection and AI model state |

---

## 📊 Sample Queries to Try

1. *"Show all students with CGPA greater than 8."*
2. *"Top 5 products by total sales revenue."*
3. *"Average salary per corporate department."*
4. *"List low stock products under 50 units."*
5. *"Total enrollments per course sorted by popularity."*

---

## 🛡️ License

M.Tech Academic Project - Free & Open Source.
