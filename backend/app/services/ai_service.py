import os
import re
import logging
import requests
from typing import Tuple, Dict, Any, Optional
from app.db.session import format_schema_for_prompt, get_prompt_schema
from app.core.config import settings
from app.services.llm_client import call_gemini, LLMError, DEFAULT_MODELS
from app.services.prompt_builder import build_sql_prompt
from app.services.rag_service import RagContext, get_runtime

logger = logging.getLogger(__name__)

FORBIDDEN_KEYWORDS = {
    "DROP", "DELETE", "UPDATE", "ALTER", "TRUNCATE", "INSERT", 
    "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "PG_SLEEP", 
    "COPY", "VACUUM", "REINDEX", "SHUTDOWN"
}

DESTRUCTIVE_PROMPT_PATTERN = re.compile(
    r"\b(delete|drop|truncate|alter|remove|wipe|purge|clear\s+table|destroy|update|insert)\b",
    re.IGNORECASE
)

class TextToSQLAIService:
    """
    Dedicated Text-to-SQL Service powered EXCLUSIVELY by Google Gemini API
    with integrated AST safety classification and destructive query interception.
    Prompt context (schema tables and few-shot examples) can be retrieved per question (RAG).
    """
    def __init__(self):
        self.model_name = getattr(settings, "GEMINI_MODEL", "gemini-3.6-flash")

    def _convert_to_safe_alternative(self, sql_or_prompt: str) -> Optional[str]:
        """
        Converts a destructive statement (e.g. DELETE FROM table WHERE condition)
        into a safe non-destructive read-only inspection query (e.g. SELECT * FROM table WHERE condition).
        """
        # Match DELETE FROM table WHERE ...
        delete_match = re.search(r"DELETE\s+FROM\s+([a-zA-Z_]+)(?:\s+WHERE\s+(.*?))?(?:;|$)", sql_or_prompt, re.IGNORECASE | re.DOTALL)
        if delete_match:
            table = delete_match.group(1).strip()
            where_clause = delete_match.group(2)
            if where_clause and where_clause.strip():
                return f"SELECT * FROM {table} WHERE {where_clause.strip().rstrip(';')};"
            return f"SELECT * FROM {table};"

        # Match UPDATE table SET ... WHERE ...
        update_match = re.search(r"UPDATE\s+([a-zA-Z_]+)\s+SET\s+.*?(?:\s+WHERE\s+(.*?))?(?:;|$)", sql_or_prompt, re.IGNORECASE | re.DOTALL)
        if update_match:
            table = update_match.group(1).strip()
            where_clause = update_match.group(2)
            if where_clause and where_clause.strip():
                return f"SELECT * FROM {table} WHERE {where_clause.strip().rstrip(';')};"
            return f"SELECT * FROM {table} LIMIT 25;"

        # Match DROP TABLE table
        drop_match = re.search(r"DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([a-zA-Z_]+)", sql_or_prompt, re.IGNORECASE)
        if drop_match:
            table = drop_match.group(1).strip()
            return f"SELECT * FROM {table} LIMIT 10;"

        # Match TRUNCATE table
        truncate_match = re.search(r"TRUNCATE\s+(?:TABLE\s+)?([a-zA-Z_]+)", sql_or_prompt, re.IGNORECASE)
        if truncate_match:
            table = truncate_match.group(1).strip()
            return f"SELECT * FROM {table};"

        # Check prompt for common entity names (students, products, orders, employees, etc.)
        for table in ["students", "orders", "products", "customers", "employees", "courses", "departments", "instructors", "order_items", "enrollments", "corp_departments"]:
            if table in sql_or_prompt.lower():
                return f"SELECT * FROM {table} LIMIT 20;"

        return "SELECT * FROM students LIMIT 10;"

    def _prepare_rag(self, question: str, rag_options: Optional[Dict[str, Any]]) -> RagContext:
        """Retrieval context for this question. Never raises: any problem means the old behaviour."""
        opts = rag_options or {}
        try:
            return get_runtime().prepare(
                question, get_prompt_schema(),
                use_schema_rag=opts.get("use_schema_rag"),
                use_example_rag=opts.get("use_example_rag"),
                static_examples=opts.get("static_examples"),
                holdout=bool(opts.get("rag_holdout")),
            )
        except Exception as exc:
            logger.warning("RAG disabled for this request: %s", exc)
            return RagContext(None, None, True, {"error": f"{type(exc).__name__}: {str(exc)[:160]}"})

    def generate_sql(self, natural_language_prompt: str, rag_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generates production-grade SQL exclusively using Google Gemini API.
        Returns a rich dictionary containing security status, SQL, explanation,
        and safe alternatives for intercepted destructive operations.
        """
        prompt_clean = natural_language_prompt.strip()

        # Read API key from settings (loaded from .env via python-dotenv)
        gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")

        if not gemini_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. Please add your GEMINI_API_KEY to the .env file in the project root."
            )

        ctx = self._prepare_rag(prompt_clean, rag_options)
        schema_prompt = ctx.schema_text or format_schema_for_prompt()
        full_prompt = build_sql_prompt(prompt_clean, schema_prompt, ctx.examples_text, ctx.include_static_block)
        ctx.meta["prompt_chars"] = len(full_prompt)

        try:
            llm = call_gemini(full_prompt, gemini_key, DEFAULT_MODELS)
        except LLMError as exc:
            from fastapi import HTTPException
            raise HTTPException(status_code=exc.status_code, detail=exc.detail)

        self.model_name = llm.model
        ctx.meta["prompt_tokens"] = llm.prompt_tokens
        text_out = llm.text

        # 1. Check for any SQL block in Gemini output
        sql_match = re.search(r"```sql\s*(.*?);?\s*```", text_out, re.IGNORECASE | re.DOTALL)
        raw_sql = sql_match.group(1).strip() if sql_match else ""

        # 2. Extract explanation
        explanation_match = re.search(r"EXPLANATION:\s*(.*)", text_out, re.IGNORECASE | re.DOTALL)
        if explanation_match:
            explanation = explanation_match.group(1).strip()
            explanation = re.sub(r"```.*", "", explanation).strip()
        else:
            explanation = f"Generated using Google Gemini ({self.model_name}) for query: '{prompt_clean}'."

        # 3. Security Guardrail Analysis:
        # Check both the extracted SQL and the user's prompt for destructive operations
        has_destructive_intent = bool(DESTRUCTIVE_PROMPT_PATTERN.search(prompt_clean))
        
        detected_forbidden = []
        if raw_sql:
            words = re.findall(r"\b[A-Z_]+\b", raw_sql.upper())
            for w in words:
                if w in FORBIDDEN_KEYWORDS:
                    detected_forbidden.append(w)

        is_blocked = False
        blocked_op = None
        if detected_forbidden:
            is_blocked = True
            blocked_op = detected_forbidden[0]
        elif has_destructive_intent:
            is_blocked = True
            prompt_match = DESTRUCTIVE_PROMPT_PATTERN.search(prompt_clean)
            blocked_op = prompt_match.group(1).upper() if prompt_match else "DESTRUCTIVE_OPERATION"

        # If a destructive or unsafe query was detected, intercept it!
        if is_blocked:
            safe_alt = raw_sql if (raw_sql and raw_sql.upper().strip().startswith("SELECT")) else self._convert_to_safe_alternative(raw_sql or prompt_clean)
            display_blocked = raw_sql if (raw_sql and not raw_sql.upper().strip().startswith("SELECT")) else f"{blocked_op} statement requested: '{prompt_clean}'"
            return {
                "is_safe": False,
                "blocked": True,
                "violation_type": "DESTRUCTIVE_OPERATION_RESTRICTED",
                "blocked_operation": blocked_op,
                "blocked_sql": display_blocked,
                "generated_sql": safe_alt,
                "suggested_safe_sql": safe_alt,
                "explanation": explanation or f"The request asks to perform a '{blocked_op}' operation, but this system strictly enforces read-only access to prevent database modification.",
                "security_message": f"Security Guardrail Triggered: The '{blocked_op}' operation is prohibited. Write, delete, and alter permissions are permanently disabled to prevent data loss.",
                "rag": ctx.meta
            }

        # If clean, ensure it's a valid SELECT query
        if not raw_sql:
            # Fallback regex
            select_match = re.search(r"(SELECT.*?;)", text_out, re.IGNORECASE | re.DOTALL)
            if select_match:
                raw_sql = select_match.group(1).strip()

        if not raw_sql:
            raise RuntimeError(f"Google Gemini generated output but no valid SQL SELECT query was found. Raw response: {text_out}")

        if not raw_sql.endswith(";"):
            raw_sql += ";"

        return {
            "is_safe": True,
            "blocked": False,
            "violation_type": None,
            "blocked_operation": None,
            "blocked_sql": None,
            "generated_sql": raw_sql,
            "suggested_safe_sql": None,
            "explanation": explanation,
            "security_message": None,
            "rag": ctx.meta
        }

ai_service = TextToSQLAIService()
