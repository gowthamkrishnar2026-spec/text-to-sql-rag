"""
Prompt assembly for the Text-to-SQL model (pure functions, no I/O).

With `include_static_block=True` and no retrieved examples, `build_sql_prompt` produces
exactly the prompt the application used before RAG existed (legacy mode).
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

INTRO = (
    "You are an expert Text-to-SQL AI assistant for a secure relational database environment. "
    "IMPORTANT SECURITY RULE: This environment strictly enforces READ-ONLY access. "
    "You must ONLY produce read-only SQL queries (SELECT or WITH ... SELECT). "
    "If the user asks to DELETE, DROP, UPDATE, TRUNCATE, INSERT, ALTER, or modify data in any way, "
    "you must NOT generate a destructive statement. Instead, explain that modifications are restricted "
    "and provide the equivalent non-destructive SELECT query that previews the records that would have been targeted.\n\n"
)

# Hand-written, project-specific guidance used before RAG. It names every table, so it is
# switched off whenever retrieval is active.
STATIC_DOMAIN_GUIDELINES = (
    "1. University Domain: 'students' (student_id, first_name, last_name, email, department_id, cgpa, enrollment_year), 'departments', 'instructors', 'courses', 'enrollments'.\n"
    "   - 'Show all students with CGPA greater than 8': SELECT student_id, first_name, last_name, cgpa FROM students WHERE cgpa > 8.0 ORDER BY cgpa DESC;\n"
    "   - 'Show instructor names and their department budget': SELECT i.name, d.department_name, d.budget FROM instructors i JOIN departments d ON i.department_id = d.department_id;\n"
    "   - 'Show students who got grade A or A+ in any course': SELECT DISTINCT s.student_id, s.first_name, s.last_name FROM students s JOIN enrollments e ON s.student_id = e.student_id WHERE e.grade IN ('A', 'A+');\n"
    "2. Corporate Domain: 'corp_departments' (dept_id, dept_name, location) and 'employees' (emp_id, emp_name, job_title, dept_id, hire_date, salary).\n"
    "   - 'Show all corporate departments with their locations': SELECT dept_id, dept_name, location FROM corp_departments;\n"
    "   - 'List employees hired after 2020 with their department name': SELECT e.emp_name, e.job_title, cd.dept_name, e.hire_date FROM employees e JOIN corp_departments cd ON e.dept_id = cd.dept_id WHERE e.hire_date > '2020-01-01' ORDER BY e.hire_date ASC;\n"
    "   - 'Total salary expenditure per department': SELECT cd.dept_name, SUM(e.salary) AS total_expenditure FROM corp_departments cd JOIN employees e ON cd.dept_id = e.dept_id GROUP BY cd.dept_name ORDER BY total_expenditure DESC;\n"
    "   - 'Show the highest paid employee in each department': SELECT cd.dept_name, e.emp_name, e.salary FROM employees e JOIN corp_departments cd ON e.dept_id = cd.dept_id WHERE e.salary = (SELECT MAX(e2.salary) FROM employees e2 WHERE e2.dept_id = e.dept_id);\n"
    "3. E-Commerce Domain: 'customers', 'products', 'orders', 'order_items'. Total revenue is SUM(oi.quantity * oi.price_per_unit).\n"
)

COLUMN_RULE = "Always select the specific columns requested by the user prompt rather than SELECT *."

RESPONSE_FORMAT = (
    "Respond strictly in the following format:\n"
    "SQL:\n"
    "```sql\n"
    "SELECT ...;\n"
    "```\n"
    "EXPLANATION:\n"
    "Your plain English explanation here.\n"
)


def _col_name(col_def: str) -> str:
    return col_def.split(" ", 1)[0]


def format_schema_ddl(schema: Dict[str, Dict[str, Any]], tables: Optional[List[str]] = None,
                      include_keys: bool = True) -> str:
    """
    Render schema entries as `CREATE TABLE ...;` lines.

    `schema[table]` needs `detailed_columns` (or `columns`) and optionally `primary_keys`
    and `foreign_keys_struct` ([{columns, ref_table, ref_columns}]).
    With include_keys=False the output matches the pre-RAG format (no PK/FK info).
    """
    names = list(tables) if tables is not None else list(schema.keys())
    lines: List[str] = []
    for table in names:
        info = schema.get(table)
        if not info:
            continue
        cols = list(info.get("detailed_columns") or info.get("columns") or [])
        if include_keys:
            pk = set(info.get("primary_keys") or [])
            cols = [c + " PRIMARY KEY" if (_col_name(c) in pk and "PRIMARY KEY" not in c) else c for c in cols]
            for fk in info.get("foreign_keys_struct") or []:
                if fk.get("ref_table"):
                    cols.append(
                        f"FOREIGN KEY ({', '.join(fk.get('columns', []))}) "
                        f"REFERENCES {fk['ref_table']}({', '.join(fk.get('ref_columns', []))})"
                    )
        desc = info.get("description")
        if desc:
            lines.append(f"-- {desc}")
        lines.append(f"CREATE TABLE {table} ({', '.join(cols)});")
        hints = info.get("value_hints") or {}
        if hints:
            parts = ["{} IN ({})".format(c, ", ".join("'" + v.replace("'", "''") + "'" for v in vals))
                     for c, vals in hints.items()]
            lines.append(f"-- Allowed values in {table}: " + "; ".join(parts))
    return "\n".join(lines)


def format_examples(examples: Iterable[Any]) -> str:
    """Render retrieved examples (objects with .question, .sql, .source) for the prompt."""
    examples = list(examples)
    if not examples:
        return ""
    out = [
        "Reference examples (question -> SQL). Examples marked (other database) were written for "
        "different tables: use them only as a guide to SQL structure and never copy their table or "
        "column names. Only use tables and columns from the Database Schema above."
    ]
    for ex in examples:
        tag = "this database" if getattr(ex, "source", "") == "project" else "other database"
        out.append(f"Q ({tag}): {ex.question}\nSQL: {ex.sql.strip().rstrip(';')};")
    return "\n\n".join(out)


def build_sql_prompt(question: str, schema_text: str, examples_text: Optional[str] = None,
                     include_static_block: bool = True, dialect: Optional[str] = None) -> str:
    parts = [INTRO, f"Database Schema:\n{schema_text}\n\n"]
    if examples_text:
        parts.append(f"{examples_text}\n\n")
    if include_static_block:
        parts.append("Key Schema Mapping Guidelines:\n")
        parts.append(STATIC_DOMAIN_GUIDELINES)
        parts.append(f"4. Column Selection: {COLUMN_RULE}\n")
        if dialect:
            parts.append(f"5. SQL dialect: write {dialect}-compatible SQL.\n")
    else:
        parts.append("Guidelines:\n")
        parts.append(f"1. Column Selection: {COLUMN_RULE}\n")
        if dialect:
            parts.append(f"2. SQL dialect: write {dialect}-compatible SQL.\n")
    parts.append("\n")
    parts.append(RESPONSE_FORMAT)
    system_instruction = "".join(parts)
    return f"{system_instruction}\n\nUser Question: {question.strip()}"
