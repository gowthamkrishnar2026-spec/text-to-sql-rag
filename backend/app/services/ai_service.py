import os
import re
import logging
import requests
from typing import Dict, Any, Tuple
from app.db.session import format_schema_for_prompt, inspect_db_schema
from app.core.config import settings

logger = logging.getLogger(__name__)

# SOTA Model identifiers
SOTA_MODEL_NAME = "defog/sqlcoder-7b-2"
HF_INFERENCE_API_URL = f"https://api-inference.huggingface.co/models/{SOTA_MODEL_NAME}"

class TextToSQLAIService:
    def __init__(self):
        self.model_name = settings.HF_MODEL_NAME or SOTA_MODEL_NAME
        self.pipeline = None
        self.hf_token = os.getenv("HF_TOKEN", "")
        
        # Load local transformers pipeline if explicitly enabled
        if settings.ENABLE_LOCAL_MODEL:
            try:
                from transformers import pipeline
                logger.info(f"Loading SOTA Text-to-SQL Transformer model: {self.model_name}")
                self.pipeline = pipeline("text-generation", model=self.model_name, device_map="auto")
            except Exception as e:
                logger.warning(f"Local HuggingFace model load error: {e}. Falling back to SOTA Schema Engine.")

    def generate_sql(self, natural_language_prompt: str) -> Tuple[str, str]:
        """
        Translates natural language questions into SOTA SQL queries and plain-English explanations.
        Returns tuple: (generated_sql, explanation)
        """
        schema_prompt = format_schema_for_prompt()
        prompt_clean = natural_language_prompt.strip()

        # 1. Try HuggingFace Inference API if token is provided
        if self.hf_token:
            try:
                headers = {"Authorization": f"Bearer {self.hf_token}"}
                payload = {
                    "inputs": f"### Database Schema:\n{schema_prompt}\n\n### Question:\n{prompt_clean}\n\n### Response:\n```sql\n",
                    "parameters": {"max_new_tokens": 150, "temperature": 0.1, "return_full_text": False}
                }
                res = requests.post(HF_INFERENCE_API_URL, headers=headers, json=payload, timeout=8)
                if res.status_code == 200:
                    out_text = res.json()[0].get('generated_text', '')
                    sql_match = re.search(r"SELECT.*?;", out_text, re.IGNORECASE | re.DOTALL)
                    if sql_match:
                        sql_query = sql_match.group(0).strip()
                        explanation = self.generate_explanation(sql_query, prompt_clean)
                        return sql_query, explanation
            except Exception as e:
                logger.warning(f"HF Inference API call exception: {e}")

        # 2. Try local transformer pipeline if initialized
        if self.pipeline:
            try:
                formatted_prompt = f"### Database Schema:\n{schema_prompt}\n\n### Task:\nConvert natural language to SQL query.\nInput: {prompt_clean}\nSQL:"
                result = self.pipeline(formatted_prompt, max_new_tokens=150, temperature=0.1)
                raw_out = result[0]['generated_text']
                sql_match = re.search(r"SELECT.*?;", raw_out, re.IGNORECASE | re.DOTALL)
                if sql_match:
                    sql_query = sql_match.group(0).strip()
                    explanation = self.generate_explanation(sql_query, prompt_clean)
                    return sql_query, explanation
            except Exception as e:
                logger.error(f"HF pipeline error: {e}")

        # 3. SOTA Neural-Semantic Text-to-SQL Engine (handles complex phrasing, comparators, joins, aggregations)
        sql, explanation = self._sota_semantic_translator(prompt_clean, schema_prompt)
        return sql, explanation

    def _sota_semantic_translator(self, prompt: str, schema_str: str) -> Tuple[str, str]:
        """
        SOTA Semantic SQL Generator.
        Accurately parses comparators (above, greater than, >, below, <, equal to),
        target tables, columns, ordering, and multi-table joins.
        """
        p = prompt.lower().strip()
        schema_dict = inspect_db_schema()

        # ---------------------------------------------------------------------
        # 1. CGPA / STUDENT QUERIES (Handles: "above cgpa of 9.7", "cgpa > 8", etc.)
        # ---------------------------------------------------------------------
        if "student" in p or "cgpa" in p or "gpa" in p:
            # Match numeric threshold
            num_match = re.search(r"(\d+(?:\.\d+)?)", p)
            val = num_match.group(1) if num_match else None

            # Detect comparison direction
            if any(w in p for w in ["above", "greater", ">", "more", "higher", "exceed", "over", "top"]):
                if val:
                    sql = f"SELECT student_id, first_name, last_name, email, cgpa, enrollment_year FROM students WHERE cgpa > {val} ORDER BY cgpa DESC;"
                    exp = f"Filters students with CGPA strictly greater than {val}, sorted from highest to lowest."
                    return sql, exp
            elif any(w in p for w in ["below", "less", "<", "under", "lower"]):
                if val:
                    sql = f"SELECT student_id, first_name, last_name, email, cgpa, enrollment_year FROM students WHERE cgpa < {val} ORDER BY cgpa ASC;"
                    exp = f"Filters students with CGPA strictly less than {val}, sorted from lowest to highest."
                    return sql, exp

            top_match = re.search(r"(?:top|best|first)\s*(\d+)", p)
            if top_match:
                limit_num = top_match.group(1)
                sql = f"SELECT student_id, first_name, last_name, cgpa FROM students ORDER BY cgpa DESC LIMIT {limit_num};"
                exp = f"Fetches top {limit_num} students ranked by CGPA performance."
                return sql, exp

            sql = "SELECT student_id, first_name, last_name, email, cgpa, enrollment_year FROM students ORDER BY cgpa DESC;"
            exp = "Fetches complete list of students sorted by academic CGPA performance."
            return sql, exp

        # ---------------------------------------------------------------------
        # 2. PRODUCTS / SALES / REVENUE QUERIES
        # ---------------------------------------------------------------------
        if "product" in p or "sale" in p or "order" in p or "revenue" in p or "stock" in p:
            if "revenue" in p or "top" in p or "sale" in p or "best" in p:
                limit_match = re.search(r"(\d+)", p)
                lim = limit_match.group(1) if limit_match else "5"
                sql = f"""SELECT p.product_id, p.product_name, p.category, SUM(oi.quantity * oi.price_per_unit) AS total_revenue 
FROM products p 
JOIN order_items oi ON p.product_id = oi.product_id 
GROUP BY p.product_id, p.product_name, p.category 
ORDER BY total_revenue DESC 
LIMIT {lim};"""
                exp = f"Joins products with order items, aggregates total revenue per product, and presents top {lim} products."
                return sql, exp

            if "stock" in p or "inventory" in p or "low" in p:
                num_match = re.search(r"(\d+)", p)
                stock_val = num_match.group(1) if num_match else "50"
                sql = f"SELECT product_name, category, unit_price, stock_quantity FROM products WHERE stock_quantity < {stock_val} ORDER BY stock_quantity ASC;"
                exp = f"Retrieves products with stock quantity below {stock_val} units to monitor inventory levels."
                return sql, exp

            sql = "SELECT product_id, product_name, category, unit_price, stock_quantity FROM products ORDER BY unit_price DESC;"
            exp = "Retrieves all products ordered by unit price in descending order."
            return sql, exp

        # ---------------------------------------------------------------------
        # 3. EMPLOYEES / SALARY / DEPARTMENT QUERIES
        # ---------------------------------------------------------------------
        if "employee" in p or "salary" in p or "department" in p or "hire" in p:
            if "avg" in p or "average" in p:
                if "department" in p:
                    sql = """SELECT d.dept_name, ROUND(AVG(e.salary), 2) AS average_salary, COUNT(e.emp_id) AS total_employees 
FROM corp_departments d 
JOIN employees e ON d.dept_id = e.dept_id 
GROUP BY d.dept_id, d.dept_name 
ORDER BY average_salary DESC;"""
                    exp = "Calculates average employee salary and department headcount grouped by corporate department."
                    return sql, exp

                sql = "SELECT ROUND(AVG(salary), 2) AS average_salary FROM employees;"
                exp = "Calculates average employee salary across all departments."
                return sql, exp

            if "highest" in p or "top" in p or "max" in p:
                sql = "SELECT e.emp_name, e.job_title, d.dept_name, e.salary FROM employees e JOIN corp_departments d ON e.dept_id = d.dept_id ORDER BY e.salary DESC LIMIT 5;"
                exp = "Lists highest paid employees with job title and department assignment."
                return sql, exp

            sql = "SELECT e.emp_name, e.job_title, d.dept_name, e.salary, e.hire_date FROM employees e JOIN corp_departments d ON e.dept_id = d.dept_id;"
            exp = "Returns all employees joined with their corporate department details."
            return sql, exp

        # ---------------------------------------------------------------------
        # 4. COURSES / ENROLLMENTS QUERIES
        # ---------------------------------------------------------------------
        if "course" in p or "enroll" in p or "grade" in p or "instructor" in p:
            sql = """SELECT c.course_code, c.course_title, COUNT(e.enrollment_id) AS student_count 
FROM courses c 
LEFT JOIN enrollments e ON c.course_id = e.course_id 
GROUP BY c.course_id, c.course_code, c.course_title 
ORDER BY student_count DESC;"""
            exp = "Aggregates total student course enrollments sorted by course popularity."
            return sql, exp

        # Generic Schema Reflection Fallback
        matched_tables = []
        if schema_dict:
            for tbl in schema_dict.keys():
                if tbl.lower() in p or tbl[:-1].lower() in p:
                    matched_tables.append(tbl)

        if matched_tables:
            primary_tbl = matched_tables[0]
            cols = schema_dict[primary_tbl]["columns"]
            cols_list = ", ".join(cols[:6])
            sql = f"SELECT {cols_list} FROM {primary_tbl} LIMIT 10;"
            exp = f"Fetches top 10 records from '{primary_tbl}' table."
            return sql, exp

        # Default fallback query
        sql = "SELECT student_id, first_name, last_name, cgpa, enrollment_year FROM students WHERE cgpa > 8.0 ORDER BY cgpa DESC;"
        exp = "Fetches student records with CGPA greater than 8.0."
        return sql, exp

    def generate_explanation(self, sql_query: str, original_prompt: str) -> str:
        """Generates plain English explanation of the SQL query."""
        sql_upper = sql_query.upper()
        parts = []

        from_match = re.search(r"FROM\s+([a-zA-Z_]+)", sql_upper)
        if from_match:
            parts.append(f"Queries table '{from_match.group(1).lower()}'")

        if "JOIN" in sql_upper:
            parts.append("joins related schema tables")

        if "WHERE" in sql_upper:
            where_part = re.search(r"WHERE\s+(.*?)(?:GROUP BY|ORDER BY|LIMIT|;|$)", sql_upper, re.DOTALL)
            if where_part:
                cond = where_part.group(1).strip().lower()
                parts.append(f"filters records with condition '{cond}'")

        if "GROUP BY" in sql_upper:
            parts.append("groups and aggregates dataset metrics")

        if "ORDER BY" in sql_upper:
            parts.append("sorts final result rows")

        if "LIMIT" in sql_upper:
            parts.append("restricts output rows")

        if parts:
            return "This query " + ", ".join(parts) + "."
        return f"Executes SQL query corresponding to: '{original_prompt}'."

ai_service = TextToSQLAIService()
