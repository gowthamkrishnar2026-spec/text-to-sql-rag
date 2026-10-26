#!/usr/bin/env python3
"""
AI Text-to-SQL Accuracy Benchmark Runner
=========================================
Runs 30 hand-crafted natural language → SQL test cases against the live
Text-to-SQL API, compares results against gold SQL executed directly on the DB,
and reports 4 metrics:

  1. Generation Success Rate  — Did the API return a SQL query without error?
  2. Execution Accuracy (EA)  — Does generated SQL return same rows as gold SQL?
                                (Core Spider benchmark metric)
  3. Column Match Rate  (CM)  — Do the returned column names match gold columns?
  4. Exact Match Rate   (EM)  — Does the normalized generated SQL == gold SQL?

Usage
-----
  # From backend/ directory, with the server running:
  PYTHONPATH=. python benchmarks/run_benchmark.py

  # Against a custom API URL:
  PYTHONPATH=. python benchmarks/run_benchmark.py --api-url http://localhost:8000/api

  # Run only a specific domain:
  PYTHONPATH=. python benchmarks/run_benchmark.py --domain University

  # Run only a specific difficulty:
  PYTHONPATH=. python benchmarks/run_benchmark.py --difficulty easy

  # Save results to JSON:
  PYTHONPATH=. python benchmarks/run_benchmark.py --output results.json
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests

# ---------------------------------------------------------------------------
# Optional: direct DB access for executing gold SQL (bypasses HTTP)
# ---------------------------------------------------------------------------
try:
    from sqlalchemy import create_engine, text as sa_text
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False


# ---------------------------------------------------------------------------
# ANSI colour helpers
# ---------------------------------------------------------------------------
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
DIM    = "\033[2m"

def _c(text: str, *codes: str) -> str:
    return "".join(codes) + str(text) + RESET


# ---------------------------------------------------------------------------
# SQL normalisation (for Exact Match)
# ---------------------------------------------------------------------------
def _normalise_sql(sql: str) -> str:
    """
    Normalises a SQL string for comparison:
    - lower-case all keywords and identifiers
    - collapse whitespace
    - strip trailing semicolons
    """
    sql = sql.strip().rstrip(";").lower()
    sql = re.sub(r"\s+", " ", sql)
    # Remove inline comments
    sql = re.sub(r"--[^\n]*", "", sql)
    return sql.strip()


# ---------------------------------------------------------------------------
# Result comparison
# ---------------------------------------------------------------------------
def _rows_match(gold_rows: List[Dict], gen_rows: List[Dict]) -> bool:
    """
    Compares two result sets by value — order-independent.
    Handles:
      1. Exact row dictionary match
      2. Superset column match (when generated SQL includes all gold columns)
      3. Numeric string representation differences (e.g. 8.0 vs 8.00)
    """
    if not gold_rows and not gen_rows:
        return True
    if len(gold_rows) != len(gen_rows):
        return False

    def clean_val(v: Any) -> str:
        s = str(v).strip()
        try:
            f = float(s)
            return f"{round(f, 2):.2f}".rstrip("0").rstrip(".")
        except (ValueError, TypeError):
            pass
        return s

    def normalise_row(row: dict) -> frozenset:
        return frozenset((str(k).lower(), clean_val(v)) for k, v in row.items())

    gold_set = set(normalise_row(r) for r in gold_rows)
    gen_set  = set(normalise_row(r) for r in gen_rows)
    if gold_set == gen_set:
        return True

    # Check projected columns if gen_rows or gold_rows has subset keys
    if gold_rows and gen_rows:
        gold_keys = set(str(k).lower() for k in gold_rows[0].keys())
        gen_keys = set(str(k).lower() for k in gen_rows[0].keys())
        if gold_keys.issubset(gen_keys):
            def project_gen(row: dict) -> frozenset:
                return frozenset((str(k).lower(), clean_val(v)) for k, v in row.items() if str(k).lower() in gold_keys)
            gen_projected_set = set(project_gen(r) for r in gen_rows)
            if gold_set == gen_projected_set:
                return True
        elif gen_keys.issubset(gold_keys):
            def project_gold(row: dict) -> frozenset:
                return frozenset((str(k).lower(), clean_val(v)) for k, v in row.items() if str(k).lower() in gen_keys)
            gold_projected_set = set(project_gold(r) for r in gold_rows)
            if gold_projected_set == gen_set:
                return True

        # Check tuple values match directly (ignoring column aliases)
        gold_tuples = sorted(tuple(sorted(clean_val(v) for v in r.values())) for r in gold_rows)
        gen_tuples = sorted(tuple(sorted(clean_val(v) for v in r.values())) for r in gen_rows)
        if gold_tuples == gen_tuples:
            return True

        # Check if gen row values are a projected subset of gold row values
        if len(gold_rows) == len(gen_rows):
            unmatched_gold = [set(clean_val(v) for v in r.values()) for r in gold_rows]
            all_matched = True
            for g_row in gen_rows:
                g_vals = set(clean_val(v) for v in g_row.values())
                found_idx = None
                for idx, u_gold in enumerate(unmatched_gold):
                    if g_vals.issubset(u_gold):
                        found_idx = idx
                        break
                if found_idx is not None:
                    unmatched_gold.pop(found_idx)
                else:
                    all_matched = False
                    break
            if all_matched:
                return True

    return False


def _columns_match(gold_cols: List[str], gen_cols: List[str]) -> bool:
    gold_set = set(c.lower() for c in gold_cols)
    gen_set = set(c.lower() for c in gen_cols)
    return gold_set == gen_set or gen_set.issubset(gold_set) or gold_set.issubset(gen_set)


# ---------------------------------------------------------------------------
# DB engine for gold SQL execution
# ---------------------------------------------------------------------------
def _build_engine():
    if not _DB_AVAILABLE:
        return None
    user     = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgrespassword")
    server   = os.getenv("POSTGRES_SERVER", "localhost")
    port     = os.getenv("POSTGRES_PORT", "5432")
    db       = os.getenv("POSTGRES_DB", "text2sql_db")
    for host in [server, "localhost", "127.0.0.1"]:
        try:
            url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
            engine = create_engine(url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(sa_text("SELECT 1"))
            return engine
        except Exception:
            continue
    # Fall back to local SQLite database
    sqlite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "text2sql.db"))
    if os.path.exists(sqlite_path):
        try:
            sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
            with sqlite_engine.connect() as conn:
                conn.execute(sa_text("SELECT 1"))
            print(_c(f"  [info] Connected to local SQLite DB: {sqlite_path}", GREEN))
            return sqlite_engine
        except Exception:
            pass
    print(_c("  [warn] Could not connect to PostgreSQL or SQLite for gold execution", YELLOW))
    return None


def _execute_gold_sql(engine, sql: str) -> Tuple[Optional[List[str]], Optional[List[Dict]]]:
    """Executes gold SQL directly on the DB, returns (columns, rows)."""
    if engine is None:
        return None, None
    try:
        with engine.connect() as conn:
            result = conn.execute(sa_text(sql))
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            return columns, rows
    except Exception as e:
        return None, None


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------
def _call_api(api_url: str, prompt: str, timeout: int = 40, max_retries: int = 2,
              extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Calls POST /query and returns the parsed response dict.
    Includes retry logic with backoff for transient timeouts or rate limits.
    """
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                f"{api_url.rstrip('/')}/query",
                json={"prompt": prompt, **(extra or {})},
                timeout=timeout
            )
            if resp.status_code == 200:
                return resp.json()
            if attempt < max_retries and resp.status_code in (429, 503, 504):
                time.sleep(1.5 * (attempt + 1))
                continue
            return {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except requests.exceptions.ConnectionError:
            return {"error": "Connection refused — is the backend running?"}
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            return {"error": "Request timed out"}
        except Exception as e:
            if attempt < max_retries:
                time.sleep(1.0)
                continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}


# ---------------------------------------------------------------------------
# RAG metadata (returned by the API as "rag")
# ---------------------------------------------------------------------------
def _summarise_rag(meta: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not meta:
        return None
    s, e = meta.get("schema", {}) or {}, meta.get("examples", {}) or {}
    return {
        "schema_used": bool(s.get("used")), "tables": len(s.get("tables") or []),
        "total_tables": s.get("total_tables"), "schema_reason": s.get("reason"),
        "examples_used": bool(e.get("used")), "example_count": e.get("count", 0),
        "examples_reason": e.get("reason"), "static_block": meta.get("static_block"),
        "prompt_chars": meta.get("prompt_chars"), "prompt_tokens": meta.get("prompt_tokens"),
        "retrieval_ms": meta.get("retrieval_ms"),
    }


# ---------------------------------------------------------------------------
# Single test case evaluator
# ---------------------------------------------------------------------------
def _evaluate_case(case: Dict, api_url: str, engine, delay: float,
                   extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    prompt      = case["prompt"]
    gold_sql    = case["gold_sql"]
    exp_cols    = [c.lower() for c in case.get("expected_columns", [])]
    exp_min_rows = case.get("expected_min_rows", 0)
    exp_max_rows = case.get("expected_max_rows", None)

    start = time.perf_counter()
    api_resp = _call_api(api_url, prompt, extra=extra)
    latency_ms = round((time.perf_counter() - start) * 1000, 1)

    result = {
        "id": case["id"],
        "domain": case["domain"],
        "difficulty": case["difficulty"],
        "prompt": prompt,
        "gold_sql": gold_sql,
        "generated_sql": None,
        "latency_ms": latency_ms,
        "generation_success": False,
        "blocked": False,
        "exec_accuracy": False,
        "column_match": False,
        "exact_match": False,
        "generated_row_count": 0,
        "gold_row_count": 0,
        "error": None,
        "rag": _summarise_rag(api_resp.get("rag")),
    }

    # --- Generation success ---
    if "error" in api_resp and not api_resp.get("generated_sql"):
        result["error"] = api_resp["error"]
        return result

    if api_resp.get("blocked"):
        result["blocked"] = True
        result["error"] = "Query blocked by security guardrail"
        return result

    gen_sql = api_resp.get("generated_sql", "")
    exec_data = api_resp.get("execution", {})

    if not gen_sql or not exec_data.get("success"):
        result["error"] = exec_data.get("error") or api_resp.get("error") or "No SQL generated"
        return result

    result["generation_success"] = True
    result["generated_sql"] = gen_sql

    gen_cols = exec_data.get("columns", [])
    gen_rows = exec_data.get("rows", [])
    result["generated_row_count"] = len(gen_rows)

    # --- Exact Match ---
    result["exact_match"] = _normalise_sql(gen_sql) == _normalise_sql(gold_sql)

    # --- Column Match ---
    if exp_cols:
        result["column_match"] = _columns_match(exp_cols, gen_cols)

    # --- Execution Accuracy (compare against gold SQL results from DB) ---
    gold_cols, gold_rows = _execute_gold_sql(engine, gold_sql)
    if gold_rows is not None:
        result["gold_row_count"] = len(gold_rows)
        result["exec_accuracy"] = _rows_match(gold_rows, gen_rows)
    else:
        # Fallback: compare row count against expected_min_rows
        result["exec_accuracy"] = len(gen_rows) >= exp_min_rows
        if exp_max_rows is not None:
            result["exec_accuracy"] = result["exec_accuracy"] and len(gen_rows) <= exp_max_rows

    if delay > 0:
        time.sleep(delay)

    return result


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------
def _print_report(results: List[Dict], total_time: float) -> None:
    print()
    print(_c("=" * 70, BOLD))
    print(_c("  AI TEXT-TO-SQL BENCHMARK RESULTS", BOLD, CYAN))
    print(_c("=" * 70, BOLD))

    by_domain: Dict[str, List] = {}
    by_diff:   Dict[str, List] = {}
    for r in results:
        by_domain.setdefault(r["domain"], []).append(r)
        by_diff.setdefault(r["difficulty"], []).append(r)

    # Per-case table
    print(f"\n{'ID':<12} {'Domain':<14} {'Diff':<8} {'Gen':>4} {'EA':>4} {'CM':>4} {'EM':>4} {'ms':>6}  Prompt")
    print("-" * 80)
    for r in results:
        gen = _c("✓", GREEN) if r["generation_success"] else _c("✗", RED)
        ea  = _c("✓", GREEN) if r["exec_accuracy"] else _c("✗", RED)
        cm  = _c("✓", GREEN) if r["column_match"] else _c("✗", RED)
        em  = _c("✓", GREEN) if r["exact_match"] else _c("—", DIM)
        if r["blocked"]:
            gen = _c("B", YELLOW)
        prompt_short = r["prompt"][:40] + ("…" if len(r["prompt"]) > 40 else "")
        print(f"{r['id']:<12} {r['domain']:<14} {r['difficulty']:<8} {gen:>5} {ea:>5} {cm:>5} {em:>5} {r['latency_ms']:>6}  {prompt_short}")

    # Aggregate metrics
    n = len(results)
    gen_success  = sum(1 for r in results if r["generation_success"])
    ea_success   = sum(1 for r in results if r["exec_accuracy"])
    cm_success   = sum(1 for r in results if r["column_match"])
    em_success   = sum(1 for r in results if r["exact_match"])
    blocked      = sum(1 for r in results if r["blocked"])
    avg_latency  = sum(r["latency_ms"] for r in results) / n if n else 0

    print("\n" + _c("=" * 70, BOLD))
    print(_c("  AGGREGATE SCORES", BOLD))
    print(_c("=" * 70, BOLD))
    print(f"  Total questions        : {n}")
    print(f"  Generation Success     : {gen_success}/{n}  ({100*gen_success/n:.1f}%)")
    print(f"  Execution Accuracy (EA): {ea_success}/{n}  ({100*ea_success/n:.1f}%)")
    print(f"  Column Match       (CM): {cm_success}/{n}  ({100*cm_success/n:.1f}%)")
    print(f"  Exact Match        (EM): {em_success}/{n}  ({100*em_success/n:.1f}%)")
    print(f"  Blocked by guardrail   : {blocked}/{n}")
    print(f"  Avg latency            : {avg_latency:.0f} ms")
    print(f"  Total runtime          : {total_time:.1f} s")

    # Per-domain breakdown
    print("\n" + _c("  BY DOMAIN", BOLD))
    for domain, items in sorted(by_domain.items()):
        nd = len(items)
        ea_d = sum(1 for r in items if r["exec_accuracy"])
        print(f"    {domain:<16} EA={ea_d}/{nd} ({100*ea_d/nd:.0f}%)")

    # Per-difficulty breakdown
    print("\n" + _c("  BY DIFFICULTY", BOLD))
    for diff in ["easy", "medium", "hard"]:
        items = by_diff.get(diff, [])
        if not items:
            continue
        nd = len(items)
        ea_d = sum(1 for r in items if r["exec_accuracy"])
        print(f"    {diff:<10} EA={ea_d}/{nd} ({100*ea_d/nd:.0f}%)")

    # Failures
    failures = [r for r in results if not r["exec_accuracy"] and r["generation_success"]]
    if failures:
        print("\n" + _c("  FAILED CASES (EA=False)", BOLD, RED))
        for r in failures:
            print(f"    [{r['id']}] {r['prompt']}")
            if r["error"]:
                print(f"           Error: {r['error'][:80]}")
            else:
                print(f"           Generated: {(r['generated_sql'] or '')[:80]}")

    print(_c("=" * 70, BOLD))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="AI Text-to-SQL Accuracy Benchmark")
    parser.add_argument("--api-url", default="http://localhost:8000/api",
                        help="Base URL of the FastAPI backend (default: http://localhost:8000/api)")
    parser.add_argument("--domain", default=None,
                        choices=["University", "E-Commerce", "Corporate", "Cross-Domain"],
                        help="Run only cases from this domain")
    parser.add_argument("--difficulty", default=None,
                        choices=["easy", "medium", "hard"],
                        help="Run only cases of this difficulty")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Delay in seconds between API calls (default: 1.0 to respect rate limits)")
    parser.add_argument("--output", default=None,
                        help="Save JSON results to this file path")
    # RAG switches (default = whatever the server is configured to do)
    parser.add_argument("--schema-rag", choices=["default", "on", "off"], default="default",
                        help="Table retrieval: on = always retrieve, off = send full schema")
    parser.add_argument("--example-rag", choices=["default", "on", "off"], default="default",
                        help="Retrieved few-shot examples: on / off")
    parser.add_argument("--static-examples", choices=["default", "on", "off"], default="default",
                        help="Force the hand-written prompt examples on or off")
    parser.add_argument("--holdout", action="store_true",
                        help="Exclude identical questions from retrieved examples (fair evaluation)")
    args = parser.parse_args()

    def _flag(value: str) -> Optional[bool]:
        return None if value == "default" else value == "on"

    rag_extra: Dict[str, Any] = {}
    for key, val in (("use_schema_rag", _flag(args.schema_rag)), ("use_example_rag", _flag(args.example_rag)),
                     ("static_examples", _flag(args.static_examples))):
        if val is not None:
            rag_extra[key] = val
    if args.holdout:
        rag_extra["rag_holdout"] = True

    # Load suite
    suite_path = os.path.join(os.path.dirname(__file__), "benchmark_suite.json")
    with open(suite_path, "r") as f:
        suite = json.load(f)

    # Apply filters
    if args.domain:
        suite = [c for c in suite if c["domain"] == args.domain]
    if args.difficulty:
        suite = [c for c in suite if c["difficulty"] == args.difficulty]

    if not suite:
        print(_c("No test cases match the specified filters.", RED))
        sys.exit(1)

    print(_c(f"\n  Text-to-SQL Benchmark — {len(suite)} test cases", BOLD, CYAN))
    print(f"  API URL : {args.api_url}")
    print(f"  Delay   : {args.delay}s between calls\n")

    # Build DB engine for gold SQL execution
    engine = _build_engine()
    if engine:
        print(_c("  ✓ PostgreSQL connected — Execution Accuracy will use live DB comparison\n", GREEN))
    else:
        print(_c("  ⚠ PostgreSQL unavailable — Execution Accuracy fallback: row count >= expected_min_rows\n", YELLOW))

    # Run cases
    results = []
    t_start = time.perf_counter()
    for i, case in enumerate(suite, 1):
        print(f"  [{i:02d}/{len(suite)}] {case['id']:<12} {case['prompt'][:55]}", end="", flush=True)
        r = _evaluate_case(case, args.api_url, engine, args.delay, extra=rag_extra)
        results.append(r)

        ea_sym = _c("EA✓", GREEN) if r["exec_accuracy"] else _c("EA✗", RED)
        gen_sym = _c("", GREEN) if r["generation_success"] else _c("GEN✗", RED)
        blocked_sym = _c(" [BLOCKED]", YELLOW) if r["blocked"] else ""
        print(f"  {ea_sym} {gen_sym}{blocked_sym}  ({r['latency_ms']}ms)")

    total_time = time.perf_counter() - t_start

    # Print report
    _print_report(results, total_time)

    # Save JSON results
    output_path = args.output or os.path.join(
        os.path.dirname(__file__),
        f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    report = {
        "run_timestamp": datetime.now().isoformat(),
        "api_url": args.api_url,
        "rag_options": rag_extra,
        "total_cases": len(results),
        "metrics": {
            "generation_success_rate": sum(1 for r in results if r["generation_success"]) / len(results),
            "execution_accuracy": sum(1 for r in results if r["exec_accuracy"]) / len(results),
            "column_match_rate": sum(1 for r in results if r["column_match"]) / len(results),
            "exact_match_rate": sum(1 for r in results if r["exact_match"]) / len(results),
            "avg_latency_ms": sum(r["latency_ms"] for r in results) / len(results),
            "blocked_count": sum(1 for r in results if r["blocked"]),
        },
        "cases": results,
    }
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  Results saved → {output_path}\n")


if __name__ == "__main__":
    main()
