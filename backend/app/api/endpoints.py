from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.ai_service import ai_service
from app.services.executor_service import executor_service
from app.services.export_service import export_service
from app.services.sql_validator import sanitize_and_validate_sql, SQLValidationError
from app.db.session import inspect_db_schema, engine
from app.core.config import settings

router = APIRouter()

# In-memory history store (can be persisted to PostgreSQL history table)
QUERY_HISTORY: List[Dict[str, Any]] = [
    {
        "id": "1",
        "prompt": "Show all students with CGPA greater than 8.",
        "sql_query": "SELECT student_id, first_name, last_name, email, cgpa, enrollment_year FROM students WHERE cgpa > 8.0 ORDER BY cgpa DESC;",
        "row_count": 5,
        "execution_time_ms": 1.45,
        "timestamp": datetime.now().isoformat(),
        "status": "success"
    },
    {
        "id": "2",
        "prompt": "Top products by total sales revenue",
        "sql_query": "SELECT p.product_name, SUM(oi.quantity * oi.price_per_unit) AS total_revenue FROM products p JOIN order_items oi ON p.product_id = oi.product_id GROUP BY p.product_id, p.product_name ORDER BY total_revenue DESC LIMIT 5;",
        "row_count": 4,
        "execution_time_ms": 2.10,
        "timestamp": datetime.now().isoformat(),
        "status": "success"
    }
]

# Request / Response Schemas
class GenerateSQLRequest(BaseModel):
    prompt: str = Field(..., example="Show all students with CGPA greater than 8.")

class GenerateSQLResponse(BaseModel):
    prompt: str
    generated_sql: str
    explanation: str

class ExecuteQueryRequest(BaseModel):
    sql_query: str = Field(..., example="SELECT * FROM students WHERE cgpa > 8;")

class ProcessQueryRequest(BaseModel):
    prompt: str = Field(..., example="List top 5 products by revenue.")

class ExportRequest(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    sql_query: Optional[str] = ""
    format: str = Field(..., example="csv") # csv, excel, pdf

from sqlalchemy import text

@router.get("/health")
def health_check():
    """Health check endpoint confirming DB connection and system state."""
    db_connected = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
            db_connected = True
    except Exception as e:
        db_connected = False

    return {
        "status": "online",
        "database_connected": db_connected,
        "ai_model": settings.HF_MODEL_NAME if hasattr(settings, 'HF_MODEL_NAME') else "cssuchahn/sqlcoder-7b-2",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/schema")
def get_database_schema():
    """Fetches full database schema for UI inspection and model prompting."""
    schema_info = inspect_db_schema()
    return {"tables": schema_info}

@router.post("/generate-sql", response_model=GenerateSQLResponse)
def generate_sql(request: GenerateSQLRequest):
    """Converts natural language input into valid SQL."""
    try:
        sql, explanation = ai_service.generate_sql(request.prompt)
        return GenerateSQLResponse(
            prompt=request.prompt,
            generated_sql=sql,
            explanation=explanation
        )
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
    Natural Language -> AI SQL Generation -> Validation -> Postgres Execution -> Chart Recommendation -> History Log
    """
    # 1. AI SQL Generation
    generated_sql, explanation = ai_service.generate_sql(request.prompt)
    
    # 2. Execution & Validation
    exec_result = executor_service.execute_query(generated_sql)
    
    # 3. Log to History
    history_entry = {
        "id": str(len(QUERY_HISTORY) + 1),
        "prompt": request.prompt,
        "sql_query": exec_result.get("sql_query", generated_sql),
        "row_count": exec_result.get("row_count", 0),
        "execution_time_ms": exec_result.get("execution_time_ms", 0),
        "timestamp": datetime.now().isoformat(),
        "status": "success" if exec_result.get("success") else "error"
    }
    QUERY_HISTORY.insert(0, history_entry)
    
    return {
        "prompt": request.prompt,
        "generated_sql": generated_sql,
        "explanation": explanation,
        "execution": exec_result
    }

@router.get("/history")
def get_query_history():
    """Returns past query history."""
    return {"history": QUERY_HISTORY}

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
