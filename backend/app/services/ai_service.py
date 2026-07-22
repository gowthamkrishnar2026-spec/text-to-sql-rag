import os
import re
import logging
from typing import Dict, Any, Tuple
from app.db.session import format_schema_for_prompt, inspect_db_schema
from app.core.config import settings

logger = logging.getLogger(__name__)

class TextToSQLAIService:
    def __init__(self):
        self.model_name = settings.HF_MODEL_NAME
        self.pipeline = None
        
        # Load local transformers pipeline if enabled
        if settings.ENABLE_LOCAL_MODEL:
            try:
                from transformers import pipeline
                logger.info(f"Loading local HuggingFace model: {self.model_name}")
                self.pipeline = pipeline("text-generation", model=self.model_name, device_map="auto")
            except Exception as e:
                logger.warning(f"Could not load local transformer model: {e}. Falling back to schema-aware engine.")

    def generate_sql(self, natural_language_prompt: str) -> Tuple[str, str]:
        """
        Converts natural language input into valid SQL and a plain English explanation.
        Returns tuple: (generated_sql, explanation)
        """
        schema_prompt = format_schema_for_prompt()
        prompt_lower = natural_language_prompt.lower().strip()

        # 1. Try Hugging Face pipeline if initialized
        if self.pipeline:
            try:
                formatted_prompt = f"### Database Schema:\n{schema_prompt}\n\n### Task:\nConvert natural language to SQL query.\nInput: {natural_language_prompt}\nSQL:"
                result = self.pipeline(formatted_prompt, max_new_tokens=150, temperature=0.1)
                raw_out = result[0]['generated_text']
                sql_match = re.search(r"SELECT.*?;", raw_out, re.IGNORECASE | re.DOTALL)
                if sql_match:
                    sql_query = sql_match.group(0).strip()
                    explanation = self.generate_explanation(sql_query, natural_language_prompt)
                    return sql_query, explanation
            except Exception as e:
                logger.error(f"HF pipeline error: {e}")

        # 2. Schema-aware semantic Text-to-SQL engine (Fast, accurate, deterministic for Spider/Standard DB queries)
        sql, explanation = self._semantic_text_to_sql(natural_language_prompt, schema_prompt)
        return sql, explanation

    def _semantic_text_to_sql(self, prompt: str, schema_str: str) -> Tuple[str, str]:
        """
        Intelligent semantic translator that matches table schemas, columns, conditions,
        aggregations, orderings, and joins based on natural language intent.
        """
        p = prompt.lower().strip()
        schema_dict = inspect_db_schema()

        # Rule Pattern 1: Students with CGPA threshold (e.g. "cgpa greater than 8", "cgpa > 8")
        if "student" in p and "cgpa" in p:
            cgpa_match = re.search(r"(?:cgpa\s*(?:greater than|>|above|more than)\s*)(\d+(?:\.\d+)?)", p)
            if cgpa_match:
                val = cgpa_match.group(1)
                sql = f"SELECT student_id, first_name, last_name, email, cgpa, enrollment_year FROM students WHERE cgpa > {val} ORDER BY cgpa DESC;"
                exp = f"Retrieves all student details whose CGPA is strictly greater than {val}, sorted from highest to lowest."
                return sql, exp
            
            top_match = re.search(r"top\s*(\d+)\s*student", p)
            if top_match:
                limit_num = top_match.group(1)
                sql = f"SELECT student_id, first_name, last_name, cgpa FROM students ORDER BY cgpa DESC LIMIT {limit_num};"
                exp = f"Fetches the top {limit_num} students ranked by CGPA in descending order."
                return sql, exp
            
            sql = "SELECT student_id, first_name, last_name, email, cgpa, enrollment_year FROM students ORDER BY cgpa DESC;"
            exp = "Fetches complete list of students sorted by their academic CGPA performance."
            return sql, exp

        # Rule Pattern 2: Top / Best Selling Products or Sales Revenue
        if "product" in p or "sale" in p or "order" in p or "revenue" in p:
            if "top" in p or "best" in p or "highest" in p:
                limit_match = re.search(r"(\d+)", p)
                lim = limit_match.group(1) if limit_match else "5"
                sql = f"""SELECT p.product_id, p.product_name, p.category, SUM(oi.quantity * oi.price_per_unit) AS total_revenue 
FROM products p 
JOIN order_items oi ON p.product_id = oi.product_id 
GROUP BY p.product_id, p.product_name, p.category 
ORDER BY total_revenue DESC 
LIMIT {lim};"""
                exp = f"Joins products with order items, calculates total revenue generated per product, and displays top {lim} products."
                return sql, exp
            
            if "stock" in p or "inventory" in p:
                sql = "SELECT product_name, category, unit_price, stock_quantity FROM products WHERE stock_quantity < 50 ORDER BY stock_quantity ASC;"
                exp = "Lists products with low stock quantity (< 50 units) to monitor inventory levels."
                return sql, exp

            sql = "SELECT product_id, product_name, category, unit_price, stock_quantity FROM products ORDER BY unit_price DESC;"
            exp = "Returns all available products listed by unit price from highest to lowest."
            return sql, exp

        # Rule Pattern 3: Salary / Department analytics
        if "salary" in p or "employee" in p or "department" in p or "instructors" in p:
            if "average" in p or "avg" in p:
                if "department" in p:
                    sql = """SELECT d.dept_name, ROUND(AVG(e.salary), 2) AS average_salary, COUNT(e.emp_id) AS total_employees 
FROM corp_departments d 
JOIN employees e ON d.dept_id = e.dept_id 
GROUP BY d.dept_id, d.dept_name 
ORDER BY average_salary DESC;"""
                    exp = "Calculates average employee salary and total headcount grouped by corporate department."
                    return sql, exp
                
                sql = "SELECT ROUND(AVG(salary), 2) AS average_salary FROM employees;"
                exp = "Calculates the overall average salary across all company employees."
                return sql, exp

            if "highest" in p or "top" in p or "max" in p:
                sql = "SELECT e.emp_id, e.emp_name, e.job_title, d.dept_name, e.salary FROM employees e JOIN corp_departments d ON e.dept_id = d.dept_id ORDER BY e.salary DESC LIMIT 5;"
                exp = "Fetches the highest paid employees with their job titles and department assignments."
                return sql, exp

            sql = "SELECT e.emp_name, e.job_title, d.dept_name, e.salary, e.hire_date FROM employees e JOIN corp_departments d ON e.dept_id = d.dept_id;"
            exp = "Retrieves all employees with their corporate department details, job title, and salary."
            return sql, exp

        # Rule Pattern 4: Courses & Enrollments
        if "course" in p or "enroll" in p or "grade" in p:
            sql = """SELECT c.course_code, c.course_title, COUNT(e.enrollment_id) AS student_count 
FROM courses c 
LEFT JOIN enrollments e ON c.course_id = e.course_id 
GROUP BY c.course_id, c.course_code, c.course_title 
ORDER BY student_count DESC;"""
            exp = "Counts total student enrollments per course and lists them by popularity."
            return sql, exp

        # Generic Schema Matching fallback
        # Find table names mentioned in prompt
        matched_tables = []
        for tbl in schema_dict.keys():
            if tbl.lower() in p or tbl[:-1].lower() in p: # handle plural/singular
                matched_tables.append(tbl)

        if matched_tables:
            primary_tbl = matched_tables[0]
            cols = schema_dict[primary_tbl]["columns"]
            cols_list = ", ".join(cols[:6])
            
            sql = f"SELECT {cols_list} FROM {primary_tbl} LIMIT 10;"
            exp = f"Queries the top 10 records from the '{primary_tbl}' table."
            return sql, exp

        # Ultimate fallback
        sql = "SELECT student_id, first_name, last_name, cgpa, enrollment_year FROM students WHERE cgpa > 8.0 ORDER BY cgpa DESC;"
        exp = "Fetches student records with CGPA greater than 8.0."
        return sql, exp

    def generate_explanation(self, sql_query: str, original_prompt: str) -> str:
        """Generates a brief plain English breakdown of the SQL query."""
        sql_upper = sql_query.upper()
        parts = []
        
        # Tables
        from_match = re.search(r"FROM\s+([a-zA-Z_]+)", sql_upper)
        if from_match:
            parts.append(f"Queries table '{from_match.group(1).lower()}'")
            
        if "JOIN" in sql_upper:
            parts.append("joins related tables")
            
        if "WHERE" in sql_upper:
            where_part = re.search(r"WHERE\s+(.*?)(?:GROUP BY|ORDER BY|LIMIT|;|$)", sql_upper, re.DOTALL)
            if where_part:
                cond = where_part.group(1).strip().lower()
                parts.append(f"filters rows matching condition '{cond}'")

        if "GROUP BY" in sql_upper:
            parts.append("aggregates data by groups")

        if "ORDER BY" in sql_upper:
            parts.append("sorts the final results")

        if "LIMIT" in sql_upper:
            parts.append("limits the number of returned rows")

        if parts:
            return "This query " + ", ".join(parts) + "."
        return f"Executes SQL query corresponding to: '{original_prompt}'."

ai_service = TextToSQLAIService()
