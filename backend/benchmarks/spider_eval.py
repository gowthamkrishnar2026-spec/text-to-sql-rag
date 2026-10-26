#!/usr/bin/env python3
"""
Spider Benchmark Integration
=============================
Implements the Spider evaluation methodology for measuring Text-to-SQL accuracy.

What is Spider?
---------------
Spider is the standard academic benchmark for cross-domain text-to-SQL
evaluation by Yale NLP (https://yale-nlp.github.io/spider/).
It measures two key metrics:
  - Exact Set Match (EM): Are all SQL clauses structurally equivalent?
  - Execution Accuracy (EA): Does generated SQL return the same result set
                              as the gold SQL?

This file provides:
  1. A curated Spider-style dataset adapted to this project's schema
     (30 questions in Spider format — no external download needed)
  2. An optional adapter to run against the real Spider dev.json
     (requires manual download from https://yale-nlp.github.io/spider/)
  3. The Spider evaluation metrics: Exact Set Match + Execution Accuracy
  4. A full CLI runner that scores the live Text-to-SQL API

Usage
-----
  # Run the built-in adapted dataset (no download required):
  PYTHONPATH=. python benchmarks/spider_eval.py

  # Run against the real Spider dev set (requires download):
  PYTHONPATH=. python benchmarks/spider_eval.py --spider-dev /path/to/spider/dev.json

  # Save results:
  PYTHONPATH=. python benchmarks/spider_eval.py --output spider_results.json

  # Target a different API:
  PYTHONPATH=. python benchmarks/spider_eval.py --api-url http://localhost:8000/api
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import requests

# ---------------------------------------------------------------------------
# Optional DB access for Execution Accuracy
# ---------------------------------------------------------------------------
try:
    from sqlalchemy import create_engine, text as sa_text
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False


# ---------------------------------------------------------------------------
# ANSI colours
# ---------------------------------------------------------------------------
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
DIM    = "\033[2m"

def _c(text, *codes):
    return "".join(codes) + str(text) + RESET


# ---------------------------------------------------------------------------
# Built-in Spider-adapted dataset
# (Same format as Spider dev.json — works with real Spider loader too)
# ---------------------------------------------------------------------------
SPIDER_ADAPTED_DATASET = [
    # ---------- UNIVERSITY ----------
    {
        "db_id": "text2sql",
        "question": "How many students are there?",
        "query": "SELECT COUNT(*) FROM students;",
        "difficulty": "easy"
    },
    {
        "db_id": "text2sql",
        "question": "What are the names of all departments?",
        "query": "SELECT department_name FROM departments;",
        "difficulty": "easy"
    },
    {
        "db_id": "text2sql",
        "question": "Find all students whose CGPA is above 9.",
        "query": "SELECT first_name, last_name, cgpa FROM students WHERE cgpa > 9.0;",
        "difficulty": "easy"
    },
    {
        "db_id": "text2sql",
        "question": "What is the total budget across all departments?",
        "query": "SELECT SUM(budget) AS total_budget FROM departments;",
        "difficulty": "easy"
    },
    {
        "db_id": "text2sql",
        "question": "List the names and salaries of all instructors.",
        "query": "SELECT name, salary FROM instructors;",
        "difficulty": "easy"
    },
    {
        "db_id": "text2sql",
        "question": "How many courses are offered per department?",
        "query": "SELECT d.department_name, COUNT(c.course_id) AS course_count FROM departments d LEFT JOIN courses c ON d.department_id = c.department_id GROUP BY d.department_name;",
        "difficulty": "medium"
    },
    {
        "db_id": "text2sql",
        "question": "What is the average CGPA of students in Computer Science?",
        "query": "SELECT AVG(s.cgpa) AS avg_cgpa FROM students s JOIN departments d ON s.department_id = d.department_id WHERE d.department_name = 'Computer Science';",
        "difficulty": "medium"
    },
    {
        "db_id": "text2sql",
        "question": "Which instructor has the highest salary?",
        "query": "SELECT name, salary FROM instructors ORDER BY salary DESC LIMIT 1;",
        "difficulty": "medium"
    },
    {
        "db_id": "text2sql",
        "question": "Find students who enrolled in Fall 2023.",
        "query": "SELECT s.first_name, s.last_name FROM students s JOIN enrollments e ON s.student_id = e.student_id WHERE e.semester = 'Fall 2023';",
        "difficulty": "medium"
    },
    {
        "db_id": "text2sql",
        "question": "List all courses taught by Dr. Grace Hopper.",
        "query": "SELECT c.course_code, c.course_title FROM courses c JOIN instructors i ON c.instructor_id = i.instructor_id WHERE i.name = 'Dr. Grace Hopper';",
        "difficulty": "medium"
    },
    {
        "db_id": "text2sql",
        "question": "Which department has the highest average CGPA among its students?",
        "query": "SELECT d.department_name, AVG(s.cgpa) AS avg_cgpa FROM students s JOIN departments d ON s.department_id = d.department_id GROUP BY d.department_name ORDER BY avg_cgpa DESC LIMIT 1;",
        "difficulty": "hard"
    },
    {
        "db_id": "text2sql",
        "question": "Find students who are enrolled in more than one course.",
        "query": "SELECT s.first_name, s.last_name, COUNT(e.course_id) AS course_count FROM students s JOIN enrollments e ON s.student_id = e.student_id GROUP BY s.student_id, s.first_name, s.last_name HAVING COUNT(e.course_id) > 1;",
        "difficulty": "hard"
    },
    # ---------- E-COMMERCE ----------
    {
        "db_id": "text2sql",
        "question": "How many products are there?",
        "query": "SELECT COUNT(*) FROM products;",
        "difficulty": "easy"
    },
    {
        "db_id": "text2sql",
        "question": "What is the most expensive product?",
        "query": "SELECT product_name, unit_price FROM products ORDER BY unit_price DESC LIMIT 1;",
        "difficulty": "easy"
    },
    {
        "db_id": "text2sql",
        "question": "List all customers from the USA.",
        "query": "SELECT customer_name, city FROM customers WHERE country = 'USA';",
        "difficulty": "easy"
    },
    {
        "db_id": "text2sql",
        "question": "What is the total revenue from all completed orders?",
        "query": "SELECT SUM(total_amount) AS total_revenue FROM orders WHERE status = 'Completed';",
        "difficulty": "medium"
    },
    {
        "db_id": "text2sql",
        "question": "Which product has the most total units sold?",
        "query": "SELECT p.product_name, SUM(oi.quantity) AS total_sold FROM products p JOIN order_items oi ON p.product_id = oi.product_id GROUP BY p.product_name ORDER BY total_sold DESC LIMIT 1;",
        "difficulty": "medium"
    },
    {
        "db_id": "text2sql",
        "question": "Find all orders with total amount greater than 2000.",
        "query": "SELECT order_id, customer_id, total_amount, status FROM orders WHERE total_amount > 2000;",
        "difficulty": "medium"
    },
    {
        "db_id": "text2sql",
        "question": "How many distinct product categories exist?",
        "query": "SELECT COUNT(DISTINCT category) AS category_count FROM products;",
        "difficulty": "easy"
    },
    {
        "db_id": "text2sql",
        "question": "What is the average unit price of products in the Accessories category?",
        "query": "SELECT AVG(unit_price) AS avg_price FROM products WHERE category = 'Accessories';",
        "difficulty": "medium"
    },
    {
        "db_id": "text2sql",
        "question": "List customers who have placed at least one order and their total spend.",
        "query": "SELECT c.customer_name, SUM(o.total_amount) AS total_spend FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_name ORDER BY total_spend DESC;",
        "difficulty": "hard"
    },
    # ---------- CORPORATE ----------
    {
        "db_id": "text2sql",
        "question": "How many employees are there in total?",
        "query": "SELECT COUNT(*) FROM employees;",
        "difficulty": "easy"
    },
    {
        "db_id": "text2sql",
        "question": "What are the names of all corporate departments?",
        "query": "SELECT dept_name FROM corp_departments;",
        "difficulty": "easy"
    },
    {
        "db_id": "text2sql",
        "question": "Who is the highest paid employee?",
        "query": "SELECT emp_name, job_title, salary FROM employees ORDER BY salary DESC LIMIT 1;",
        "difficulty": "easy"
    },
    {
        "db_id": "text2sql",
        "question": "What is the average salary of all employees?",
        "query": "SELECT AVG(salary) AS avg_salary FROM employees;",
        "difficulty": "easy"
    },
    {
        "db_id": "text2sql",
        "question": "List employees in the Engineering department.",
        "query": "SELECT e.emp_name, e.job_title, e.salary FROM employees e JOIN corp_departments cd ON e.dept_id = cd.dept_id WHERE cd.dept_name = 'Engineering';",
        "difficulty": "medium"
    },
    {
        "db_id": "text2sql",
        "question": "Which department has the highest total salary expenditure?",
        "query": "SELECT cd.dept_name, SUM(e.salary) AS total_salary FROM employees e JOIN corp_departments cd ON e.dept_id = cd.dept_id GROUP BY cd.dept_name ORDER BY total_salary DESC LIMIT 1;",
        "difficulty": "medium"
    },
    {
        "db_id": "text2sql",
        "question": "Find employees hired between 2019 and 2021.",
        "query": "SELECT emp_name, job_title, hire_date FROM employees WHERE hire_date BETWEEN '2019-01-01' AND '2021-12-31' ORDER BY hire_date;",
        "difficulty": "medium"
    },
    {
        "db_id": "text2sql",
        "question": "How many employees does each department have?",
        "query": "SELECT cd.dept_name, COUNT(e.emp_id) AS employee_count FROM corp_departments cd LEFT JOIN employees e ON cd.dept_id = e.dept_id GROUP BY cd.dept_name ORDER BY employee_count DESC;",
        "difficulty": "medium"
    },
    {
        "db_id": "text2sql",
        "question": "Show the department name and average salary for departments with more than one employee.",
        "query": "SELECT cd.dept_name, AVG(e.salary) AS avg_salary FROM employees e JOIN corp_departments cd ON e.dept_id = cd.dept_id GROUP BY cd.dept_name HAVING COUNT(e.emp_id) > 1 ORDER BY avg_salary DESC;",
        "difficulty": "hard"
    },
    {
        "db_id": "text2sql",
        "question": "Which employee has been with the company the longest?",
        "query": "SELECT emp_name, job_title, hire_date FROM employees ORDER BY hire_date ASC LIMIT 1;",
        "difficulty": "medium"
    },
]


# ---------------------------------------------------------------------------
# Spider Exact Set Match (EM) — clause-level structural comparison
# ---------------------------------------------------------------------------
SQL_CLAUSE_KEYWORDS = [
    "select", "from", "where", "group by", "order by",
    "having", "limit", "join", "on", "as"
]

def _extract_clauses(sql: str) -> Dict[str, str]:
    """
    Splits a normalised SQL string into clause segments for structural comparison.
    This implements a simplified version of the Spider EM clause comparison.
    """
    sql = sql.lower().strip().rstrip(";")
    clauses = {}

    # Extract SELECT
    m = re.search(r"^select\s+(.*?)(?=\s+from\s)", sql, re.DOTALL)
    if m:
        clauses["select"] = re.sub(r"\s+", " ", m.group(1).strip())

    # Extract FROM (up to WHERE/GROUP/ORDER/HAVING/LIMIT)
    m = re.search(r"\bfrom\s+(.*?)(?=\s+(?:where|group by|order by|having|limit|$))", sql, re.DOTALL)
    if m:
        clauses["from"] = re.sub(r"\s+", " ", m.group(1).strip())

    # Extract WHERE
    m = re.search(r"\bwhere\s+(.*?)(?=\s+(?:group by|order by|having|limit|$))", sql, re.DOTALL)
    if m:
        clauses["where"] = re.sub(r"\s+", " ", m.group(1).strip())

    # Extract GROUP BY
    m = re.search(r"\bgroup by\s+(.*?)(?=\s+(?:having|order by|limit|$))", sql, re.DOTALL)
    if m:
        clauses["group_by"] = re.sub(r"\s+", " ", m.group(1).strip())

    # Extract HAVING
    m = re.search(r"\bhaving\s+(.*?)(?=\s+(?:order by|limit|$))", sql, re.DOTALL)
    if m:
        clauses["having"] = re.sub(r"\s+", " ", m.group(1).strip())

    # Extract ORDER BY
    m = re.search(r"\border by\s+(.*?)(?=\s+(?:limit|$))", sql, re.DOTALL)
    if m:
        clauses["order_by"] = re.sub(r"\s+", " ", m.group(1).strip())

    return clauses


def _exact_set_match(gold_sql: str, gen_sql: str) -> Tuple[bool, float]:
    """
    Spider Exact Set Match: checks clause-level equivalence.
    Returns (is_match, partial_score).
    partial_score = fraction of clauses that match.
    """
    gold_clauses = _extract_clauses(gold_sql)
    gen_clauses  = _extract_clauses(gen_sql)

    if not gold_clauses:
        return False, 0.0

    matched = 0
    for clause, gold_val in gold_clauses.items():
        gen_val = gen_clauses.get(clause, "")
        if gold_val == gen_val:
            matched += 1

    score = matched / len(gold_clauses)
    return score == 1.0, score


# ---------------------------------------------------------------------------
# DB engine
# ---------------------------------------------------------------------------
def _build_engine():
    if not _DB_AVAILABLE:
        return None
    user     = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgrespassword")
    server   = os.getenv("POSTGRES_SERVER", "localhost")
    port     = os.getenv("POSTGRES_PORT", "5432")
    db       = os.getenv("POSTGRES_DB", "text2sql_db")
    url = f"postgresql+psycopg2://{user}:{password}@{server}:{port}/{db}"
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(sa_text("SELECT 1"))
        return engine
    except Exception:
        # Fall back to local SQLite database
        sqlite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "text2sql.db"))
        if os.path.exists(sqlite_path):
            try:
                sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
                with sqlite_engine.connect() as conn:
                    conn.execute(sa_text("SELECT 1"))
                return sqlite_engine
            except Exception:
                pass
        return None


def _exec_sql(engine, sql: str) -> Optional[List[Tuple]]:
    if engine is None:
        return None
    try:
        with engine.connect() as conn:
            result = conn.execute(sa_text(sql))
            return [tuple(str(v) for v in row) for row in result.fetchall()]
    except Exception:
        return None


def _exec_accuracy(engine, gold_sql: str, gen_sql: str) -> bool:
    """
    Spider Execution Accuracy: gold result set == generated result set.
    Compares as order-independent sets of string-tuples.
    """
    gold_rows = _exec_sql(engine, gold_sql)
    gen_rows  = _exec_sql(engine, gen_sql)
    if gold_rows is None or gen_rows is None:
        return False
    return set(gold_rows) == set(gen_rows)


# ---------------------------------------------------------------------------
# Load real Spider dataset (optional)
# ---------------------------------------------------------------------------
def _load_spider_dev(path: str) -> List[Dict]:
    """
    Loads the real Spider dev.json. Only returns items with db_id that match
    one of the known tables in this project (approximate filter).
    Since Spider uses different DB schemas, only questions whose gold SQL
    contains table names from our schema are included.
    """
    OUR_TABLES = {
        "students", "departments", "instructors", "courses", "enrollments",
        "customers", "products", "orders", "order_items",
        "corp_departments", "employees"
    }

    with open(path, "r") as f:
        spider_data = json.load(f)

    compatible = []
    for item in spider_data:
        sql_lower = item.get("query", "").lower()
        if any(f" {t} " in sql_lower or f" {t};" in sql_lower for t in OUR_TABLES):
            compatible.append({
                "db_id": item.get("db_id", "unknown"),
                "question": item["question"],
                "query": item["query"],
                "difficulty": item.get("query_complexity", "medium"),
            })

    return compatible


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------
def _call_api(api_url: str, prompt: str) -> Dict:
    try:
        resp = requests.post(
            f"{api_url.rstrip('/')}/query",
            json={"prompt": prompt},
            timeout=30
        )
        return resp.json() if resp.status_code == 200 else {"error": f"HTTP {resp.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection refused — is the backend running?"}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Evaluate one case
# ---------------------------------------------------------------------------
def _evaluate(case: Dict, api_url: str, engine) -> Dict:
    gold_sql = case["query"]
    prompt   = case["question"]

    start = time.perf_counter()
    api_resp = _call_api(api_url, prompt)
    latency_ms = round((time.perf_counter() - start) * 1000, 1)

    result = {
        "db_id": case["db_id"],
        "difficulty": case.get("difficulty", "unknown"),
        "question": prompt,
        "gold_sql": gold_sql,
        "generated_sql": None,
        "latency_ms": latency_ms,
        "generation_success": False,
        "blocked": api_resp.get("blocked", False),
        "exec_accuracy": False,
        "exact_set_match": False,
        "partial_clause_score": 0.0,
        "error": None,
    }

    if api_resp.get("blocked"):
        result["error"] = "Blocked by security guardrail"
        return result

    gen_sql = api_resp.get("generated_sql", "")
    exec_data = api_resp.get("execution", {})

    if not gen_sql or not exec_data.get("success"):
        result["error"] = exec_data.get("error") or api_resp.get("error") or "No SQL generated"
        return result

    result["generation_success"] = True
    result["generated_sql"] = gen_sql

    # Spider Exact Set Match
    em, partial = _exact_set_match(gold_sql, gen_sql)
    result["exact_set_match"] = em
    result["partial_clause_score"] = round(partial, 2)

    # Spider Execution Accuracy
    result["exec_accuracy"] = _exec_accuracy(engine, gold_sql, gen_sql)

    return result


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def _print_report(results: List[Dict], total_time: float, dataset_name: str) -> None:
    n = len(results)
    gen_ok = sum(1 for r in results if r["generation_success"])
    ea_ok  = sum(1 for r in results if r["exec_accuracy"])
    em_ok  = sum(1 for r in results if r["exact_set_match"])
    blocked = sum(1 for r in results if r["blocked"])
    avg_partial = sum(r["partial_clause_score"] for r in results) / n if n else 0
    avg_lat = sum(r["latency_ms"] for r in results) / n if n else 0

    print()
    print(_c("=" * 70, BOLD))
    print(_c(f"  SPIDER EVALUATION RESULTS  [{dataset_name}]", BOLD, CYAN))
    print(_c("=" * 70, BOLD))

    print(f"\n{'Question':<45} {'Diff':<8} {'EA':>4} {'EM':>4}  {'Partial':>7}")
    print("-" * 70)
    for r in results:
        ea = _c("✓", GREEN) if r["exec_accuracy"] else _c("✗", RED)
        em = _c("✓", GREEN) if r["exact_set_match"] else _c("✗", RED)
        q  = r["question"][:43] + ("…" if len(r["question"]) > 43 else "")
        diff = r.get("difficulty", "?")[:7]
        print(f"{q:<45} {diff:<8} {ea:>5} {em:>5}  {r['partial_clause_score']:>6.0%}")

    print()
    print(_c("=" * 70, BOLD))
    print(_c("  SPIDER METRICS", BOLD))
    print(_c("=" * 70, BOLD))
    print(f"  Total questions             : {n}")
    print(f"  Generation Success          : {gen_ok}/{n}  ({100*gen_ok/n:.1f}%)")
    print(f"  Execution Accuracy (EA) ★   : {ea_ok}/{n}  ({100*ea_ok/n:.1f}%)")
    print(f"  Exact Set Match     (EM)    : {em_ok}/{n}  ({100*em_ok/n:.1f}%)")
    print(f"  Avg Partial Clause Score    : {avg_partial:.2%}")
    print(f"  Blocked by guardrail        : {blocked}/{n}")
    print(f"  Avg latency                 : {avg_lat:.0f} ms")
    print(f"  Total runtime               : {total_time:.1f} s")
    print()
    print(_c("  ★ Execution Accuracy is the primary Spider leaderboard metric.", DIM))
    print(_c("=" * 70, BOLD))

    # Difficulty breakdown
    by_diff: Dict[str, List] = {}
    for r in results:
        by_diff.setdefault(r.get("difficulty", "unknown"), []).append(r)

    print(_c("\n  BY DIFFICULTY", BOLD))
    for diff in ["easy", "medium", "hard"]:
        items = by_diff.get(diff, [])
        if not items:
            continue
        nd = len(items)
        ea_d = sum(1 for r in items if r["exec_accuracy"])
        em_d = sum(1 for r in items if r["exact_set_match"])
        print(f"    {diff:<10}  EA={ea_d}/{nd} ({100*ea_d/nd:.0f}%)  EM={em_d}/{nd} ({100*em_d/nd:.0f}%)")

    print(_c("=" * 70, BOLD))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Spider Benchmark Evaluation for Text-to-SQL")
    parser.add_argument("--api-url", default="http://localhost:8000/api",
                        help="FastAPI backend URL (default: http://localhost:8000/api)")
    parser.add_argument("--spider-dev", default=None,
                        help="Path to real Spider dev.json (optional). If not provided, "
                             "the built-in adapted dataset is used.")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Delay between API calls in seconds (default: 1.0)")
    parser.add_argument("--output", default=None,
                        help="Save JSON results to this file")
    args = parser.parse_args()

    # Load dataset
    if args.spider_dev:
        if not os.path.exists(args.spider_dev):
            print(_c(f"Spider dev file not found: {args.spider_dev}", RED))
            sys.exit(1)
        dataset = _load_spider_dev(args.spider_dev)
        dataset_name = f"Spider dev.json (filtered, {len(dataset)} compatible)"
        if not dataset:
            print(_c("No Spider questions matched this project's schema tables.", YELLOW))
            sys.exit(1)
    else:
        dataset = SPIDER_ADAPTED_DATASET
        dataset_name = "Built-in Adapted Dataset"

    print(_c(f"\n  Spider Evaluation — {len(dataset)} questions  [{dataset_name}]", BOLD, CYAN))
    print(f"  API URL: {args.api_url}\n")

    engine = _build_engine()
    if engine:
        db_type = "PostgreSQL" if "postgresql" in str(engine.url) else "SQLite"
        print(_c(f"  ✓ {db_type} database connected — Execution Accuracy enabled\n", GREEN))
    else:
        print(_c("  ⚠ No database connected — Execution Accuracy will be False for all\n", YELLOW))

    results = []
    t_start = time.perf_counter()

    for i, case in enumerate(dataset, 1):
        q_short = case["question"][:55]
        print(f"  [{i:02d}/{len(dataset)}] {q_short}", end="", flush=True)
        r = _evaluate(case, args.api_url, engine)
        results.append(r)

        ea = _c("EA✓", GREEN) if r["exec_accuracy"] else _c("EA✗", RED)
        em = _c("EM✓", GREEN) if r["exact_set_match"] else _c("EM✗", RED)
        blocked_sym = _c(" [BLOCKED]", YELLOW) if r["blocked"] else ""
        print(f"  {ea} {em}{blocked_sym}  ({r['latency_ms']}ms)")

        if args.delay > 0:
            time.sleep(args.delay)

    total_time = time.perf_counter() - t_start
    _print_report(results, total_time, dataset_name)

    # Save
    output_path = args.output or os.path.join(
        os.path.dirname(__file__),
        f"spider_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    n = len(results)
    report = {
        "run_timestamp": datetime.now().isoformat(),
        "dataset": dataset_name,
        "api_url": args.api_url,
        "spider_metrics": {
            "execution_accuracy":  sum(1 for r in results if r["exec_accuracy"]) / n,
            "exact_set_match":     sum(1 for r in results if r["exact_set_match"]) / n,
            "generation_success":  sum(1 for r in results if r["generation_success"]) / n,
            "avg_partial_clause":  sum(r["partial_clause_score"] for r in results) / n,
            "avg_latency_ms":      sum(r["latency_ms"] for r in results) / n,
            "blocked_count":       sum(1 for r in results if r["blocked"]),
            "total_questions":     n,
        },
        "cases": results,
    }
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  Results saved → {output_path}\n")


if __name__ == "__main__":
    main()
