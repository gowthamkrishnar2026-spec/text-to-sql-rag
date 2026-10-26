"""
Re-runs every query the user has asked before (query_history) with and without RAG, in parallel, and reports
how often the generated SQL executes and how often it returns the same rows as the SQL that was accepted earlier.

There are no hand-written gold answers for past prompts, so the reference is the most recent *successful* SQL
logged for the same prompt. That makes "match" a consistency measure, not proof of correctness; the dashboard says so.
"""
import json
import logging
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

APP_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
RESULTS_PATH = os.path.join(APP_DATA_DIR, "history_eval.json")

OFF_OPTS = {"use_example_rag": False, "use_schema_rag": False, "static_examples": True}
ON_OPTS = {"use_example_rag": True, "static_examples": False, "rag_holdout": True}


def norm_prompt(p: str) -> str:
    return re.sub(r"\W+", " ", (p or "").lower()).strip()


def collect_prompts(rows: List[Tuple[str, str, str]], limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """rows: (prompt, sql_query, status), newest first. One entry per distinct prompt, with the newest
    successful SQL as reference. Blocked prompts are kept (expected to stay blocked)."""
    seen: Dict[str, Dict[str, Any]] = {}
    for prompt, sql, status in rows:
        key = norm_prompt(prompt)
        if not key:
            continue
        item = seen.setdefault(key, {"prompt": prompt.strip(), "reference_sql": None, "blocked": False})
        if status == "success" and not item["reference_sql"] and sql:
            item["reference_sql"] = sql
        if status == "blocked":
            item["blocked"] = True
    items = [i for i in seen.values() if i["reference_sql"] or i["blocked"]]
    return items[:limit] if limit else items


def summarise(records: List[Dict[str, Any]], key: str) -> Dict[str, Any]:
    """Aggregate one configuration ('off' or 'on') over per-prompt records."""
    normal = [r for r in records if not r["expect_blocked"]]
    guard = [r for r in records if r["expect_blocked"]]
    ref = [r for r in normal if r.get("reference_ok")]
    lat = [r[key]["latency_ms"] for r in normal if r[key].get("latency_ms") is not None]
    n = len(normal)
    return {
        "prompts": n,
        "executed_ok_rate": sum(1 for r in normal if r[key]["executed"]) / n if n else 0.0,
        "match_previous_rate": sum(1 for r in ref if r[key]["match"]) / len(ref) if ref else 0.0,
        "with_reference": len(ref),
        "avg_latency_ms": sum(lat) / len(lat) if lat else 0.0,
        "errors": sum(1 for r in normal if r[key].get("error")),
        "guardrail_total": len(guard),
        "guardrail_held": sum(1 for r in guard if r[key]["blocked"]),
    }


class RagEvalService:
    def __init__(self):
        self._lock = threading.Lock()
        self.state: Dict[str, Any] = {"is_running": False, "done": 0, "total": 0, "started_at": None,
                                      "completed_at": None, "error": None}

    def get_state(self) -> Dict[str, Any]:
        return {"status": dict(self.state), "latest": self.latest()}

    @staticmethod
    def latest() -> Optional[Dict[str, Any]]:
        try:
            with open(RESULTS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    def trigger(self, limit: Optional[int] = 200, workers: int = 4) -> Dict[str, Any]:
        with self._lock:
            if self.state["is_running"]:
                return {"status": "already_running", "progress": dict(self.state)}
            self.state.update({"is_running": True, "done": 0, "total": 0, "error": None,
                               "started_at": datetime.now().isoformat(), "completed_at": None})
        threading.Thread(target=self._worker, args=(limit, max(1, min(workers, 8))), daemon=True).start()
        return {"status": "started", "started_at": self.state["started_at"]}

    # ---- internals
    def _load_history(self) -> List[Tuple[str, str, str]]:
        from sqlalchemy import text
        from app.db.session import engine
        with engine.connect() as conn:
            res = conn.execute(text("SELECT prompt, sql_query, status FROM query_history ORDER BY created_at DESC"))
            return [(r[0], r[1], r[2]) for r in res.fetchall()]

    def _run_one(self, item: Dict[str, Any], generate: Callable, execute: Callable, rows_match: Callable) -> Dict[str, Any]:
        rec: Dict[str, Any] = {"prompt": item["prompt"], "expect_blocked": item["blocked"],
                               "reference_sql": item["reference_sql"], "reference_ok": False}
        ref_rows = None
        if item["reference_sql"] and not item["blocked"]:
            r = execute(item["reference_sql"])
            if r.get("success"):
                ref_rows, rec["reference_ok"] = r.get("rows", []), True
        for key, opts in (("off", OFF_OPTS), ("on", ON_OPTS)):
            out = {"sql": None, "executed": False, "match": False, "blocked": False, "latency_ms": None, "error": None}
            t0 = time.perf_counter()
            try:
                g = generate(item["prompt"], opts)
                out["blocked"] = bool(g.get("blocked"))
                out["sql"] = g.get("generated_sql") or None
                if not out["blocked"] and out["sql"]:
                    e = execute(out["sql"])
                    out["executed"] = bool(e.get("success"))
                    out["error"] = None if out["executed"] else str(e.get("error"))[:160]
                    if out["executed"] and ref_rows is not None:
                        out["match"] = bool(rows_match(ref_rows, e.get("rows", [])))
                rag = g.get("rag") or {}
                out["examples"] = (rag.get("examples") or {}).get("count", 0) if key == "on" else 0
            except Exception as exc:  # one bad prompt must not stop the run
                out["error"] = f"{type(exc).__name__}: {str(exc)[:140]}"
            out["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            rec[key] = out
        return rec

    def _worker(self, limit: Optional[int], workers: int) -> None:
        try:
            from app.services.ai_service import ai_service
            from app.services.executor_service import executor_service
            from app.services.benchmark_service import rows_match
            items = collect_prompts(self._load_history(), limit)
            self.state["total"] = len(items)
            if not items:
                raise RuntimeError("No past queries with a usable result were found in the history.")
            gen = lambda p, o: ai_service.generate_sql(p, o)
            records: List[Dict[str, Any]] = []
            t0 = time.perf_counter()
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(self._run_one, it, gen, executor_service.execute_query, rows_match) for it in items]
                for fut in as_completed(futures):
                    records.append(fut.result())
                    self.state["done"] = len(records)
            report = {"run_timestamp": datetime.now().isoformat(), "prompts": len(records),
                      "runtime_seconds": round(time.perf_counter() - t0, 1), "workers": workers,
                      "off": summarise(records, "off"), "on": summarise(records, "on"),
                      "fixed": sum(1 for r in records if not r["expect_blocked"] and r["on"]["match"] and not r["off"]["match"]),
                      "broke": sum(1 for r in records if not r["expect_blocked"] and r["off"]["match"] and not r["on"]["match"]),
                      "records": sorted(records, key=lambda r: r["prompt"].lower())}
            os.makedirs(APP_DATA_DIR, exist_ok=True)
            with open(RESULTS_PATH, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, default=str)
            self.state.update({"is_running": False, "completed_at": datetime.now().isoformat()})
        except Exception as exc:
            logger.error("History evaluation failed: %s", exc, exc_info=True)
            self.state.update({"is_running": False, "error": str(exc)})


rag_eval_service = RagEvalService()
