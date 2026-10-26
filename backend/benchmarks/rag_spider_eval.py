#!/usr/bin/env python3
"""
RAG ablation on the official Spider dev set
===========================================
Compares four prompt configurations on real Spider dev questions, executing generated and
gold SQL against the Spider SQLite databases (execution accuracy, as on the Spider leaderboard):

  baseline   full schema, no examples
  schema     retrieved tables (+ foreign-key neighbours), no examples
  examples   full schema + retrieved question->SQL examples (Spider TRAIN set)
  both       retrieved tables + retrieved examples

Spider dev and train use different databases, so there is no train/test leakage.

Metrics per configuration
  EA            execution accuracy (generated rows == gold rows)
  table recall  share of questions where every table used by the gold SQL was in the prompt
  prompt size   average input tokens (from Gemini usage metadata when available)
  latency       average model latency (ms)

Prerequisites
  1. GEMINI_API_KEY in the project .env
  2. Spider unzipped at datasets/spider (dev.json, tables.json, database/<db_id>/<db_id>.sqlite)
  3. For the 'examples' and 'both' configs: the example index
       PYTHONPATH=. python scripts/build_rag_index.py

Usage (from backend/):
  PYTHONPATH=. python benchmarks/rag_spider_eval.py --dry-run
  PYTHONPATH=. python benchmarks/rag_spider_eval.py --limit 40
  PYTHONPATH=. python benchmarks/rag_spider_eval.py --limit 120 --min-tables 6 --configs baseline,schema,both

Rate limits: every question costs one model call per configuration. Use --limit and --delay
to stay inside the free tier. Results are saved to benchmarks/rag_spider_results_<time>.json.
"""
import argparse
import json
import os
import random
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(BACKEND, ".."))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"))
except ImportError:
    pass

from app.services.llm_client import DEFAULT_MODELS, LLMError, call_gemini  # noqa: E402
from app.services.prompt_builder import build_sql_prompt, format_schema_ddl  # noqa: E402
from app.services.rag_service import RagConfig, RagRuntime  # noqa: E402

CONFIGS = {
    "baseline": (False, False),
    "schema": (True, False),
    "examples": (False, True),
    "both": (True, True),
}


# ---------------------------------------------------------------------------
# Spider loading
# ---------------------------------------------------------------------------
def spider_schema(entry: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Convert one tables.json entry into the schema dict format used by the app."""
    tnames = entry["table_names_original"]
    cols = entry["column_names_original"]
    types = entry["column_types"]
    schema = {t: {"columns": [], "detailed_columns": [], "primary_keys": [], "foreign_keys_struct": []}
              for t in tnames}
    for i, (ti, cname) in enumerate(cols):
        if ti < 0:
            continue
        schema[tnames[ti]]["columns"].append(cname)
        schema[tnames[ti]]["detailed_columns"].append(f"{cname} {str(types[i]).upper()}")
    for pk in entry.get("primary_keys", []):
        for idx in (pk if isinstance(pk, list) else [pk]):
            ti, cname = cols[idx]
            if ti >= 0:
                schema[tnames[ti]]["primary_keys"].append(cname)
    for a, b in entry.get("foreign_keys", []):
        (ta, ca), (tb, cb) = cols[a], cols[b]
        if ta >= 0 and tb >= 0:
            schema[tnames[ta]]["foreign_keys_struct"].append(
                {"columns": [ca], "ref_table": tnames[tb], "ref_columns": [cb]})
    return schema


def load_spider(spider_dir: str, split: str):
    with open(os.path.join(spider_dir, "tables.json"), encoding="utf-8") as f:
        schemas = {e["db_id"]: spider_schema(e) for e in json.load(f)}
    with open(os.path.join(spider_dir, f"{split}.json"), encoding="utf-8") as f:
        questions = json.load(f)
    return schemas, questions


def db_path(spider_dir: str, db_id: str) -> str:
    return os.path.join(spider_dir, "database", db_id, f"{db_id}.sqlite")


def select_questions(questions, schemas, spider_dir, min_tables, limit, seed, db_ids=None):
    by_db: Dict[str, List[dict]] = defaultdict(list)
    for q in questions:
        d = q["db_id"]
        if db_ids and d not in db_ids:
            continue
        if d in schemas and len(schemas[d]) >= min_tables and os.path.exists(db_path(spider_dir, d)):
            by_db[d].append(q)
    rng = random.Random(seed)
    order = sorted(by_db)
    rng.shuffle(order)
    for d in order:
        rng.shuffle(by_db[d])
    chosen, depth = [], 0
    while len(chosen) < limit and any(len(by_db[d]) > depth for d in order):
        for d in order:
            if len(by_db[d]) > depth and len(chosen) < limit:
                chosen.append(by_db[d][depth])
        depth += 1
    return chosen


# ---------------------------------------------------------------------------
# SQL execution and comparison
# ---------------------------------------------------------------------------
def run_sqlite(path: str, sql: str, timeout_s: float = 5.0, max_rows: int = 5000):
    """Read-only execution with a time limit. Returns (rows, error)."""
    conn = None
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.text_factory = lambda b: b.decode("utf-8", errors="ignore")
        deadline = time.time() + timeout_s
        conn.set_progress_handler(lambda: 1 if time.time() > deadline else 0, 50000)
        return conn.execute(sql).fetchmany(max_rows), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"
    finally:
        if conn is not None:
            conn.close()


def _nv(v: Any) -> Any:
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        return round(float(v), 4)
    return v


def results_match(gold: List[tuple], gen: List[tuple], ordered: bool) -> bool:
    """Same rows (multiset), or same rows if columns are permuted; sequence-exact when gold has ORDER BY."""
    g = [tuple(_nv(v) for v in r) for r in gold]
    p = [tuple(_nv(v) for v in r) for r in gen]
    if len(g) != len(p):
        return False
    key = lambda row: tuple(sorted(map(repr, row)))  # noqa: E731
    if ordered:
        return g == p or [key(r) for r in g] == [key(r) for r in p]
    return Counter(g) == Counter(p) or Counter(map(key, g)) == Counter(map(key, p))


def extract_sql(text: str) -> str:
    m = re.search(r"```sql\s*(.*?);?\s*```", text, re.I | re.S)
    if m:
        return m.group(1).strip()
    m = re.search(r"((?:select|with)\b.*?)(?:;|$)", text, re.I | re.S)
    return m.group(1).strip() if m else ""


def gold_tables(schema: Dict[str, Any], gold_sql: str) -> List[str]:
    return [t for t in schema if re.search(rf"\b{re.escape(t)}\b", gold_sql, re.I)]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="RAG ablation on the Spider dev set")
    ap.add_argument("--spider-dir", default=os.path.join(ROOT, "datasets", "spider"))
    ap.add_argument("--split", default="dev")
    ap.add_argument("--configs", default="baseline,schema,examples,both")
    ap.add_argument("--min-tables", type=int, default=6, help="only databases with at least this many tables")
    ap.add_argument("--limit", type=int, default=40, help="number of questions (each costs one call per config)")
    ap.add_argument("--db-ids", default=None, help="comma-separated db_ids to restrict to")
    ap.add_argument("--k-tables", type=int, default=4)
    ap.add_argument("--max-tables", type=int, default=8)
    ap.add_argument("--k-examples", type=int, default=4)
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between model calls")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--backend", default="chroma", help="vector store for the example index")
    ap.add_argument("--store-path", default=None, help="Chroma folder (default: backend/rag_store)")
    ap.add_argument("--output", default=None)
    ap.add_argument("--dry-run", action="store_true", help="select questions and show schema sizes; no API calls")
    args = ap.parse_args()

    configs = [c.strip() for c in args.configs.split(",") if c.strip()]
    bad = [c for c in configs if c not in CONFIGS]
    if bad:
        print(f"Unknown config(s): {bad}. Choose from {list(CONFIGS)}")
        return 1

    schemas, questions = load_spider(args.spider_dir, args.split)
    db_filter = set(args.db_ids.split(",")) if args.db_ids else None
    chosen = select_questions(questions, schemas, args.spider_dir, args.min_tables, args.limit, args.seed, db_filter)
    if not chosen:
        print("No questions selected. Check --spider-dir, --min-tables and that database/*.sqlite files exist.")
        return 1
    dbs = sorted({q["db_id"] for q in chosen})
    avg_tables = sum(len(schemas[d]) for d in (q["db_id"] for q in chosen)) / len(chosen)
    print(f"Selected {len(chosen)} questions from {len(dbs)} databases (avg {avg_tables:.1f} tables per database).")

    if args.dry_run:
        for d in dbs[:10]:
            ddl = format_schema_ddl(schemas[d])
            print(f"  {d:<28} {len(schemas[d]):>3} tables, full schema = {len(ddl)} chars")
        return 0

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print("GEMINI_API_KEY is not set (add it to the project .env).")
        return 1

    from app.services.embedding_service import GeminiEmbedder

    try:
        from app.core.config import settings
        model, dim, store_default = settings.GEMINI_EMBEDDING_MODEL, settings.RAG_EMBEDDING_DIM, settings.RAG_STORE_PATH
    except Exception:
        model, dim = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"), int(os.getenv("RAG_EMBEDDING_DIM", "768"))
        store_default = os.path.join(BACKEND, "rag_store")
    embedder = GeminiEmbedder(api_key, model=model, dim=dim, timeout=30, max_retries=6, base_delay=3.0)
    cfg = RagConfig(schema_enabled=True, schema_min_tables=0, schema_top_k=args.k_tables,
                    schema_max_tables=args.max_tables, examples_enabled=True, examples_top_k=args.k_examples,
                    backend=args.backend, schema_backend="memory", store_path=args.store_path or store_default,
                    include_keys=True)
    runtime = RagRuntime(cfg, embedder_getter=lambda: embedder)

    if any(CONFIGS[c][1] for c in configs) and runtime.example_index().count() == 0:
        print("The example index is empty. Build it first:  PYTHONPATH=. python scripts/build_rag_index.py")
        return 1

    records: List[Dict[str, Any]] = []
    skipped = 0
    t_start = time.perf_counter()
    for qi, q in enumerate(chosen, 1):
        d, question, gold_sql = q["db_id"], q["question"], q["query"]
        schema = schemas[d]
        path = db_path(args.spider_dir, d)
        gold_rows, gold_err = run_sqlite(path, gold_sql)
        if gold_rows is None:
            skipped += 1
            continue
        ordered = bool(re.search(r"\border\s+by\b", gold_sql, re.I))
        needed = gold_tables(schema, gold_sql)
        print(f"[{qi:>3}/{len(chosen)}] {d:<22} {question[:60]}")

        for name in configs:
            use_schema, use_examples = CONFIGS[name]
            rec: Dict[str, Any] = {"config": name, "db_id": d, "question": question, "gold_sql": gold_sql,
                                   "generated_sql": None, "ea": False, "error": None, "infra_error": False,
                                   "total_tables": len(schema), "tables_in_prompt": len(schema),
                                   "table_recall": True, "prompt_chars": 0, "prompt_tokens": None, "latency_ms": None}
            try:
                ctx = runtime.prepare(question, schema, use_schema_rag=use_schema, use_example_rag=use_examples,
                                      static_examples=False, namespace=d)
                if use_schema and not ctx.meta["schema"]["used"]:
                    raise RuntimeError("schema retrieval failed: " + str(ctx.meta["schema"]["reason"]))
                if use_examples and not ctx.meta["examples"]["used"]:
                    raise RuntimeError("example retrieval failed: " + str(ctx.meta["examples"]["reason"]))
                schema_text = ctx.schema_text or format_schema_ddl(schema, include_keys=True)
                prompt = build_sql_prompt(question, schema_text, ctx.examples_text,
                                          include_static_block=False, dialect="SQLite")
                tables = ctx.meta["schema"]["tables"] if ctx.meta["schema"]["used"] else list(schema)
                rec.update(tables_in_prompt=len(tables), prompt_chars=len(prompt),
                           table_recall=all(t in tables for t in needed))
                for attempt in range(4):
                    try:
                        llm = call_gemini(prompt, api_key, DEFAULT_MODELS)
                        break
                    except LLMError as exc:
                        if exc.status_code in (429, 503) and attempt < 3:
                            time.sleep(20)
                            continue
                        rec["infra_error"] = True  # provider outage/quota - not a wrong answer
                        raise
                rec.update(prompt_tokens=llm.prompt_tokens, latency_ms=llm.latency_ms)
                gen_sql = extract_sql(llm.text)
                rec["generated_sql"] = gen_sql
                gen_rows, gen_err = run_sqlite(path, gen_sql) if gen_sql else (None, "no SQL returned")
                if gen_rows is None:
                    rec["error"] = gen_err
                else:
                    rec["ea"] = results_match(gold_rows, gen_rows, ordered)
            except Exception as exc:
                rec["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
            records.append(rec)
            mark = "EA✓" if rec["ea"] else "EA✗"
            print(f"      {name:<9} {mark}  tables {rec['tables_in_prompt']}/{rec['total_tables']}"
                  f"  recall {'✓' if rec['table_recall'] else '✗'}" + (f"  [{rec['error'][:60]}]" if rec["error"] else ""))
            time.sleep(args.delay)

    # ---- summary
    print("\n" + "=" * 86)
    print(f"{'config':<10} {'n':>4} {'EA':>7} {'table recall':>13} {'avg tables':>11} {'avg prompt tok':>15} {'avg ms':>8} {'errors':>7}")
    print("-" * 86)
    summary = {}
    for name in configs:
        rs = [r for r in records if r["config"] == name]
        if not rs:
            continue
        n = len(rs)
        toks = [r["prompt_tokens"] if r["prompt_tokens"] is not None else r["prompt_chars"] / 4 for r in rs if r["prompt_chars"]]
        lat = [r["latency_ms"] for r in rs if r["latency_ms"] is not None]
        s = {"n": n, "execution_accuracy": sum(r["ea"] for r in rs) / n,
             "table_recall": sum(r["table_recall"] for r in rs) / n,
             "avg_tables_in_prompt": sum(r["tables_in_prompt"] for r in rs) / n,
             "avg_prompt_tokens": sum(toks) / len(toks) if toks else None,
             "avg_latency_ms": sum(lat) / len(lat) if lat else None,
             "errors": sum(1 for r in rs if r["error"])}
        summary[name] = s
        print(f"{name:<10} {n:>4} {100*s['execution_accuracy']:>6.1f}% {100*s['table_recall']:>12.1f}% "
              f"{s['avg_tables_in_prompt']:>11.1f} {s['avg_prompt_tokens'] or 0:>15.0f} {s['avg_latency_ms'] or 0:>8.0f} {s['errors']:>7}")
    if "baseline" in summary:
        base = {(r["db_id"], r["question"]): r["ea"] for r in records if r["config"] == "baseline"}
        print("\nPaired comparison vs baseline (same questions):")
        for name in configs:
            if name == "baseline":
                continue
            rs = [r for r in records if r["config"] == name and (r["db_id"], r["question"]) in base]
            wins = sum(1 for r in rs if r["ea"] and not base[(r["db_id"], r["question"])])
            losses = sum(1 for r in rs if not r["ea"] and base[(r["db_id"], r["question"])])
            print(f"  {name:<9} fixed {wins}, broke {losses}")
    bad = {(r["db_id"], r["question"]) for r in records if r.get("infra_error")}
    keys = {(r["db_id"], r["question"]) for r in records}
    clean = keys - bad
    if bad and clean:
        print(f"\nExcluding {len(bad)} question(s) where Gemini was unavailable/over quota in any configuration "
              f"(provider failures, not wrong SQL): n = {len(clean)}")
        base_c = {(r["db_id"], r["question"]): r["ea"] for r in records if r["config"] == "baseline"}
        for name in configs:
            rs = [r for r in records if r["config"] == name and (r["db_id"], r["question"]) in clean]
            if not rs:
                continue
            line = f"  {name:<10} EA {100*sum(r['ea'] for r in rs)/len(rs):5.1f}%"
            if name != "baseline" and base_c:
                w = sum(1 for r in rs if r["ea"] and not base_c.get((r["db_id"], r["question"])))
                l = sum(1 for r in rs if not r["ea"] and base_c.get((r["db_id"], r["question"])))
                line += f"   fixed {w}, broke {l}"
            print(line)
    print(f"\nSkipped {skipped} question(s) whose gold SQL did not run. Runtime {time.perf_counter()-t_start:.0f}s.")
    print("Note: small samples are noisy; with ~40 questions a 5-point gap is within chance. Report n alongside EA.")

    out = args.output or os.path.join(HERE, f"rag_spider_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(out, "w") as f:
        json.dump({"run_timestamp": datetime.now().isoformat(), "split": args.split, "seed": args.seed,
                   "settings": {"k_tables": args.k_tables, "max_tables": args.max_tables,
                                "k_examples": args.k_examples, "min_tables": args.min_tables},
                   "summary": summary, "records": records}, f, indent=2, default=str)
    print(f"Saved -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
