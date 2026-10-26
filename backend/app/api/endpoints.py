from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.services.ai_service import ai_service
from app.services.executor_service import executor_service
from app.services.export_service import export_service
from app.services.benchmark_service import benchmark_service
from app.services.rag_eval_service import rag_eval_service
from app.services.sql_validator import sanitize_and_validate_sql, SQLValidationError
from app.db.session import inspect_db_schema, engine
from app.core.config import settings
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Helper: Persistent history via PostgreSQL query_history table
# ---------------------------------------------------------------------------

def _db_insert_history(prompt: str, sql_query: str, row_count: int, execution_time_ms: float, status: str) -> None:
    """Inserts a history entry into the query_history table. Silently ignores errors."""
    try:
        with engine.connect() as conn:
            conn.execute(
                text(
                    "INSERT INTO query_history (prompt, sql_query, row_count, execution_time_ms, status) "
                    "VALUES (:prompt, :sql_query, :row_count, :execution_time_ms, :status)"
                ),
                {
                    "prompt": prompt,
                    "sql_query": sql_query,
                    "row_count": row_count,
                    "execution_time_ms": execution_time_ms,
                    "status": status,
                }
            )
            conn.commit()
    except Exception as e:
        logger.warning(f"Could not persist query history to DB: {e}")


def _db_fetch_history() -> List[Dict[str, Any]]:
    """Reads the 50 most recent history entries from the query_history table."""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT id, prompt, sql_query, row_count, execution_time_ms, status, created_at "
                    "FROM query_history ORDER BY created_at DESC LIMIT 50"
                )
            )
            rows = result.fetchall()
            return [
                {
                    "id": str(row[0]),
                    "prompt": row[1],
                    "sql_query": row[2],
                    "row_count": row[3],
                    "execution_time_ms": row[4],
                    "status": row[5],
                    "timestamp": row[6].isoformat() if hasattr(row[6], "isoformat") else str(row[6]),
                }
                for row in rows
            ]
    except Exception as e:
        logger.warning(f"Could not read query history from DB: {e}")
        return []


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class RagOptions(BaseModel):
    """
    Optional per-request RAG switches (leave unset to use the server defaults).
    Mainly used by the benchmark scripts to compare configurations.
    """
    use_schema_rag: Optional[bool] = None    # True = always retrieve tables, False = send the full schema
    use_example_rag: Optional[bool] = None   # True = retrieve few-shot examples, False = built-in examples
    static_examples: Optional[bool] = None   # force the hand-written prompt block on/off
    rag_holdout: Optional[bool] = None       # exclude identical questions from retrieved examples (fair evaluation)

    def rag_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.model_dump().items() if v is not None}


class GenerateSQLRequest(RagOptions):
    prompt: str = Field(..., example="Show all students with CGPA greater than 8.")

class ExecuteQueryRequest(BaseModel):
    sql_query: str = Field(..., example="SELECT * FROM students WHERE cgpa > 8;")

class ProcessQueryRequest(RagOptions):
    prompt: str = Field(..., example="List top 5 products by revenue.")

class ExportRequest(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    sql_query: Optional[str] = ""
    format: str = Field(..., example="csv")  # csv, excel, pdf


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/health")
def health_check():
    """Health check endpoint confirming DB connection and system state."""
    db_connected = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
            db_connected = True
    except Exception:
        db_connected = False

    return {
        "status": "online",
        "database_connected": db_connected,
        "ai_model": ai_service.model_name,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/schema")
def get_database_schema():
    """Fetches full database schema for UI inspection and model prompting."""
    schema_info = inspect_db_schema()
    return {"tables": schema_info}


@router.post("/generate-sql")
def generate_sql(request: GenerateSQLRequest):
    """Converts natural language input into valid SQL or returns security violation."""
    try:
        return ai_service.generate_sql(request.prompt, request.rag_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-query")
def execute_query(request: ExecuteQueryRequest):
    """Validates and executes a SQL query on PostgreSQL."""
    result = executor_service.execute_query(request.sql_query)
    return result


@router.post("/query")
def process_full_query(request: ProcessQueryRequest):
    """
    Combined workflow endpoint:
    Natural Language -> AI SQL Generation & Safety Interception -> Postgres Execution -> History Log
    """
    try:
        # 1. AI SQL Generation & Security Inspection
        ai_res = ai_service.generate_sql(request.prompt, request.rag_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 2. Check if the query requested a destructive / prohibited operation
    if ai_res.get("blocked"):
        _db_insert_history(
            prompt=request.prompt,
            sql_query=ai_res.get("blocked_sql") or "[RESTRICTED OPERATION BLOCKED]",
            row_count=0,
            execution_time_ms=0,
            status="blocked",
        )

        return {
            "prompt": request.prompt,
            "is_safe": False,
            "blocked": True,
            "violation_type": ai_res.get("violation_type"),
            "blocked_operation": ai_res.get("blocked_operation"),
            "blocked_sql": ai_res.get("blocked_sql"),
            "generated_sql": ai_res.get("suggested_safe_sql") or "",
            "suggested_safe_sql": ai_res.get("suggested_safe_sql"),
            "explanation": ai_res.get("explanation"),
            "security_message": ai_res.get("security_message"),
            "rag": ai_res.get("rag"),
            "execution": {
                "success": False,
                "blocked": True,
                "sql_query": ai_res.get("blocked_sql") or "",
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": 0,
                "visualization": None,
                "error": ai_res.get("security_message")
            }
        }

    # 3. Safe query execution
    generated_sql = ai_res["generated_sql"]
    explanation = ai_res["explanation"]

    exec_result = executor_service.execute_query(generated_sql)

    is_exec_blocked = exec_result.get("blocked", False)

    # 4. Persist to DB history
    _db_insert_history(
        prompt=request.prompt,
        sql_query=exec_result.get("sql_query", generated_sql),
        row_count=exec_result.get("row_count", 0),
        execution_time_ms=exec_result.get("execution_time_ms", 0),
        status="blocked" if is_exec_blocked else ("success" if exec_result.get("success") else "error"),
    )

    return {
        "prompt": request.prompt,
        "is_safe": not is_exec_blocked,
        "blocked": is_exec_blocked,
        "violation_type": exec_result.get("violation_type"),
        "blocked_operation": None,
        "blocked_sql": None,
        "generated_sql": generated_sql,
        "suggested_safe_sql": None,
        "explanation": explanation,
        "security_message": exec_result.get("error") if is_exec_blocked else None,
        "rag": ai_res.get("rag"),
        "execution": exec_result
    }


@router.get("/history")
def get_query_history():
    """Returns past query history from the persistent database."""
    return {"history": _db_fetch_history()}


@router.post("/export")
def export_data(request: ExportRequest):
    """Exports query results to CSV, Excel, or PDF."""
    fmt = request.format.lower()

    if fmt == "csv":
        file_stream = export_service.export_to_csv(request.columns, request.rows)
        return StreamingResponse(
            file_stream,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=query_results.csv"}
        )
    elif fmt in ["excel", "xlsx"]:
        file_stream = export_service.export_to_excel(request.columns, request.rows)
        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=query_results.xlsx"}
        )
    elif fmt == "pdf":
        file_stream = export_service.export_to_pdf(request.columns, request.rows, request.sql_query or "")
        return StreamingResponse(
            file_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=query_results.pdf"}
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid export format. Must be 'csv', 'excel', or 'pdf'.")


# ---------------------------------------------------------------------------
# Benchmark Endpoints
# ---------------------------------------------------------------------------

class BenchmarkRunRequest(BaseModel):
    domain: Optional[str] = None
    difficulty: Optional[str] = None
    rag: Optional[bool] = None   # True/None = RAG on (identical questions held out), False = pre-RAG prompt


@router.get("/benchmarks")
def get_benchmarks():
    """Returns the latest benchmark evaluation metrics and case results."""
    return benchmark_service.get_latest_results()


@router.get("/benchmarks/status")
def get_benchmark_status():
    """Returns the real-time execution progress of any running benchmark."""
    return benchmark_service.get_status()


@router.post("/benchmarks/run")
def run_benchmark(request: Optional[BenchmarkRunRequest] = None):
    """Triggers an asynchronous benchmark run across Spider test cases."""
    req_domain = request.domain if request else None
    req_diff = request.difficulty if request else None
    req_rag = request.rag if request else None
    return benchmark_service.trigger_run(domain=req_domain, difficulty=req_diff, rag=req_rag)



# ---------------------------------------------------------------------------
# RAG visibility endpoints (dashboard)
# ---------------------------------------------------------------------------

class HistoryEvalRequest(BaseModel):
    limit: Optional[int] = 200
    workers: Optional[int] = 4


@router.get("/rag/status")
def rag_status():
    """Current retrieval configuration and index size, for the dashboard. Never fails the page."""
    import os
    info: Dict[str, Any] = {"available": False}
    try:
        from app.services.rag_service import get_runtime
        rt = get_runtime()
        cfg = rt.cfg
        info.update({
            "available": True,
            "examples_enabled": cfg.examples_enabled,
            "example_sources": sorted(cfg.example_sources) if cfg.example_sources else ["all"],
            "examples_top_k": cfg.examples_top_k,
            "schema_enabled": cfg.schema_enabled,
            "schema_min_tables": cfg.schema_min_tables,
            "schema_top_k": cfg.schema_top_k,
            "vector_store": cfg.backend,
            "embedding_model": getattr(settings, "GEMINI_EMBEDDING_MODEL", ""),
            "schema_descriptions": bool(getattr(settings, "SCHEMA_DESCRIPTIONS", True)),
            "schema_value_hints": bool(getattr(settings, "SCHEMA_VALUE_HINTS", True)),
            "total_tables": len(inspect_db_schema()),
        })
        try:
            ids = rt.example_index().store.ids()
            info["index_total"] = len(ids)
            info["index_project"] = sum(1 for i in ids if str(i).startswith("project-"))
            info["index_spider"] = sum(1 for i in ids if str(i).startswith("spider-"))
        except Exception as exc:
            info["index_error"] = f"{type(exc).__name__}: {str(exc)[:120]}"
    except Exception as exc:
        info["error"] = f"{type(exc).__name__}: {str(exc)[:160]}"
    return info


@router.get("/rag/ablation")
def rag_ablation():
    """Latest ablation summary (benchmarks/rag_ablation_*.json) plus the dashboard's own RAG on/off runs."""
    import glob, json, os
    out: Dict[str, Any] = {"ablation": None, "dashboard_runs": {}}
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    files = sorted(glob.glob(os.path.join(base, "benchmarks", "rag_ablation_*.json")))
    # For every configuration (A..E) keep its most recent valid run with the most questions (n >= 20
    # preferred), so a quick 10-question or failed run never hides a full 30-question result.
    best: Dict[str, Any] = {}
    for path in files:  # oldest -> newest, so newer runs win ties
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError) as exc:
            out["ablation_error"] = str(exc)[:120]
            continue
        for key, row in (d.get("summary") or {}).items():
            n = row.get("n") or 0
            if n == 0 or row.get("errors", 0) >= n or any("INVALID" in x for x in row.get("notes", [])):
                continue
            rank = (n >= 20, d.get("run_timestamp") or "")
            if key not in best or rank >= best[key][0]:
                best[key] = (rank, dict(row, run_timestamp=d.get("run_timestamp")))
    if best:
        summary = {k: best[k][1] for k in sorted(best)}
        out["ablation"] = {"run_timestamp": max(v["run_timestamp"] or "" for v in summary.values()), "summary": summary}
    for mode in ("on", "off"):
        path = os.path.join(base, "app", "data", f"benchmark_rag_{mode}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                out["dashboard_runs"][mode] = json.load(f)
        except (OSError, ValueError):
            pass
    return out


@router.get("/rag/history-eval")
def rag_history_eval():
    """Progress of the past-queries evaluation and its latest report (records trimmed)."""
    state = rag_eval_service.get_state()
    latest = state.get("latest")
    if latest:
        latest = {k: v for k, v in latest.items() if k != "records"} | {"records": latest.get("records", [])[:200]}
    return {"status": state["status"], "latest": latest}


@router.post("/rag/history-eval/run")
def rag_history_eval_run(request: Optional[HistoryEvalRequest] = None):
    """Re-runs every past prompt with and without RAG (parallel) in the background."""
    limit = request.limit if request else 200
    workers = request.workers if request and request.workers else 4
    return rag_eval_service.trigger(limit=limit, workers=workers)
