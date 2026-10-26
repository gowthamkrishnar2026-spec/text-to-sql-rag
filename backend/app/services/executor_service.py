import time
import logging
from typing import Dict, Any, List
from decimal import Decimal
import datetime
from sqlalchemy import text
from app.db.session import engine
from app.services.sql_validator import sanitize_and_validate_sql, SQLValidationError

logger = logging.getLogger(__name__)

class SQLExecutorService:
    def execute_query(self, raw_sql: str) -> Dict[str, Any]:
        """
        Validates and executes a SQL query on PostgreSQL, returning structured
        results, timing metrics, and automatic chart visualization suggestions.
        """
        start_time = time.perf_counter()

        # Step 1: Validate SQL for safety
        try:
            validated_sql = sanitize_and_validate_sql(raw_sql)
        except SQLValidationError as ve:
            return {
                "success": False,
                "blocked": True,
                "sql_query": raw_sql,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": 0,
                "visualization": None,
                "error": f"Security Guardrail Violation: {str(ve)}",
                "violation_type": "SQL_VALIDATION_ERROR"
            }
        
        try:
            with engine.connect() as connection:
                result = connection.execute(text(validated_sql))
                
                # Fetch metadata
                columns = list(result.keys())
                raw_rows = result.fetchall()
                
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                
                # Format rows as dicts for JSON API response
                rows = []
                for row in raw_rows:
                    row_dict = {}
                    for idx, col_name in enumerate(columns):
                        val = row[idx]
                        # Format Decimal/numbers/dates safely for JSON serialization
                        if isinstance(val, (datetime.date, datetime.datetime, datetime.time)):
                            val = val.isoformat()
                        elif isinstance(val, Decimal):
                            val = float(val)
                        elif isinstance(val, float):
                            val = float(val)
                        row_dict[col_name] = val
                    rows.append(row_dict)

                # Generate chart suggestions based on column types and row data
                chart_recommendation = self._recommend_visualization(columns, rows)

                return {
                    "success": True,
                    "blocked": False,
                    "sql_query": validated_sql,
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "execution_time_ms": elapsed_ms,
                    "visualization": chart_recommendation,
                    "error": None
                }

        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(f"Database execution error: {e}")
            return {
                "success": False,
                "blocked": False,
                "sql_query": raw_sql,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": elapsed_ms,
                "visualization": None,
                "error": f"Database Execution Error: {str(e)}"
            }

    def _recommend_visualization(self, columns: List[str], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes returned query columns to detect numerical vs categorical fields
        and recommend ideal Recharts configurations (Bar, Pie, Line, Area).
        """
        if not rows or not columns:
            return {"recommended_chart": "table", "x_axis": None, "y_axis": []}

        numeric_cols = []
        string_cols = []

        sample_row = rows[0]
        for col in columns:
            val = sample_row.get(col)
            if isinstance(val, (int, float, Decimal)):
                numeric_cols.append(col)
            elif isinstance(val, str):
                string_cols.append(col)

        # Default fallback
        x_axis = string_cols[0] if string_cols else columns[0]
        y_axis = numeric_cols if numeric_cols else []

        recommended_type = "bar"
        if len(numeric_cols) == 1 and len(rows) <= 7:
            recommended_type = "pie"
        elif "date" in x_axis.lower() or "year" in x_axis.lower() or "month" in x_axis.lower():
            recommended_type = "line"
        elif len(numeric_cols) > 0:
            recommended_type = "bar"
        else:
            recommended_type = "table"

        return {
            "recommended_chart": recommended_type,
            "x_axis": x_axis,
            "y_axis": y_axis,
            "numeric_columns": numeric_cols,
            "string_columns": string_cols
        }

executor_service = SQLExecutorService()
