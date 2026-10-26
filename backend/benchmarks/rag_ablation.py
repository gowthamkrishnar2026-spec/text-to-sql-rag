#!/usr/bin/env python3
"""
RAG ablation on the project's own 30-question suite (through the live API)
==========================================================================
Runs benchmark_suite.json under five prompt configurations and prints one comparison table.

  A  baseline        full schema + the hand-written prompt examples   (the pre-RAG behaviour)
  B  clean baseline  full schema, hand-written examples removed       (isolates the examples effect)
  C  + schema RAG    retrieved tables, no examples
  D  + example RAG   full schema + retrieved examples (hold-out: an identical question is never retrieved)
  E  both            retrieved tables + retrieved examples (hold-out)

How to read it
  * A vs B shows how much of the old accuracy came from examples written into the prompt
    (several of them are word-for-word benchmark questions).
  * B vs D is the honest gain from example retrieval.
  * B vs C is the effect of table retrieval. With only 11 tables, expect little or no gain here;
    schema retrieval is meant for large schemas (see rag_spider_eval.py).

Prerequisites
  * Backend running on port 8000 with GEMINI_API_KEY set
  * For D and E: the example index  ->  PYTHONPATH=. python scripts/build_rag_index.py

Usage (from backend/):
  PYTHONPATH=. python benchmarks/rag_ablation.py
  PYTHONPATH=. python benchmarks/rag_ablation.py --configs A,B,D --delay 2
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(HERE, ".."))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from benchmarks.run_benchmark import _build_engine, _evaluate_case  # noqa: E402

CONFIGS: Dict[str, Dict[str, Any]] = {
    "A": {"label": "baseline (pre-RAG prompt)",
          "opts": {"use_schema_rag": False, "use_example_rag": False, "static_examples": True}},
    "B": {"label": "clean baseline (no examples)",
          "opts": {"use_schema_rag": False, "use_example_rag": False, "static_examples": False}},
    "C": {"label": "+ schema retrieval",
          "opts": {"use_schema_rag": True, "use_example_rag": False, "static_examples": False}},
    "D": {"label": "+ example retrieval",
          "opts": {"use_schema_rag": False, "use_example_rag": True, "static_examples": False, "rag_holdout": True}},
    "E": {"label": "schema + example retrieval",
          "opts": {"use_schema_rag": True, "use_example_rag": True, "static_examples": False, "rag_holdout": True}},
}


def _avg(values: List[float]) -> float:
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else 0.0


def main() -> int:
    ap = argparse.ArgumentParser(description="RAG ablation on the 30-question project suite")
    ap.add_argument("--api-url", default="http://localhost:8000/api")
    ap.add_argument("--configs", default="A,B,C,D,E", help="comma-separated subset of A,B,C,D,E")
    ap.add_argument("--limit", type=int, default=None, help="only the first N cases (quick check)")
    ap.add_argument("--delay", type=float, default=1.5, help="seconds between API calls")
    ap.add_argument("--output", default=None)
    args = ap.parse_args()

    keys = [c.strip().upper() for c in args.configs.split(",") if c.strip()]
    unknown = [k for k in keys if k not in CONFIGS]
    if unknown:
        print(f"Unknown config(s) {unknown}; choose from {list(CONFIGS)}")
        return 1

    with open(os.path.join(HERE, "benchmark_suite.json")) as f:
        suite = json.load(f)
    if args.limit:
        suite = suite[: args.limit]
    engine = _build_engine()
    print(f"\nRAG ablation: {len(suite)} cases x {len(keys)} configurations "
          f"= {len(suite) * len(keys)} API calls (about {len(suite) * len(keys) * (args.delay + 3) / 60:.0f} min)\n")

    all_results: Dict[str, List[Dict[str, Any]]] = {}
    for key in keys:
        cfg = CONFIGS[key]
        print(f"--- {key}: {cfg['label']}  {cfg['opts']}")
        results = []
        for i, case in enumerate(suite, 1):
            r = _evaluate_case(case, args.api_url, engine, args.delay, extra=cfg["opts"])
            results.append(r)
            print(f"  [{i:02d}/{len(suite)}] {case['id']:<10} {'EA✓' if r['exec_accuracy'] else 'EA✗'}"
                  f"{'  ' + str(r['error'])[:50] if r['error'] else ''}")
        all_results[key] = results

    # ---- summary table
    print("\n" + "=" * 100)
    print(f"{'':<3}{'configuration':<30}{'EA':>8}{'col match':>11}{'exact':>8}{'avg tables':>12}"
          f"{'avg prompt tok':>16}{'avg ms':>9}  notes")
    print("-" * 100)
    summary = {}
    for key in keys:
        rs = all_results[key]
        n = len(rs)
        rag = [r.get("rag") or {} for r in rs]
        toks = [x.get("prompt_tokens") or ((x.get("prompt_chars") or 0) / 4) for x in rag if x]
        tables = [x.get("tables") if x.get("schema_used") else x.get("total_tables") for x in rag]
        notes = []
        opts = CONFIGS[key]["opts"]
        if opts.get("use_example_rag") and not any(x.get("examples_used") for x in rag):
            notes.append("INVALID: no examples were retrieved (is the index built?)")
        if opts.get("use_schema_rag") and not any(x.get("schema_used") for x in rag):
            notes.append("INVALID: schema retrieval never ran")
        s = {"label": CONFIGS[key]["label"], "n": n,
             "execution_accuracy": sum(r["exec_accuracy"] for r in rs) / n,
             "column_match": sum(r["column_match"] for r in rs) / n,
             "exact_match": sum(r["exact_match"] for r in rs) / n,
             "avg_tables_in_prompt": _avg(tables), "avg_prompt_tokens": _avg(toks),
             "avg_latency_ms": _avg([r["latency_ms"] for r in rs]),
             "errors": sum(1 for r in rs if r["error"]), "notes": notes}
        summary[key] = s
        print(f"{key:<3}{s['label']:<30}{100*s['execution_accuracy']:>7.1f}%{100*s['column_match']:>10.1f}%"
              f"{100*s['exact_match']:>7.1f}%{s['avg_tables_in_prompt']:>12.1f}{s['avg_prompt_tokens']:>16.0f}"
              f"{s['avg_latency_ms']:>9.0f}  {'; '.join(notes)}")
    print("=" * 100)
    print("EA = execution accuracy. n = %d per configuration, so one case = %.1f points." % (len(suite), 100 / len(suite)))
    print("Differences of 1-2 cases are within run-to-run noise; repeat runs before drawing conclusions.")

    out = args.output or os.path.join(HERE, f"rag_ablation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(out, "w") as f:
        json.dump({"run_timestamp": datetime.now().isoformat(), "api_url": args.api_url,
                   "summary": summary, "results": all_results}, f, indent=2, default=str)
    print(f"Saved -> {out}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
