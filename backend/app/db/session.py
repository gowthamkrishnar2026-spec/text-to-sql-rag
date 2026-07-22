from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def inspect_db_schema() -> dict:
    """
    Reflects the database schema (tables, columns, types, foreign keys)
    to generate prompt context for the Text-to-SQL AI model and UI inspector.
    """
    try:
        inspector = inspect(engine)
        schema_info = {}
        tables = inspector.get_table_names()
        
        for table in tables:
            columns = inspector.get_columns(table)
            fks = inspector.get_foreign_keys(table)
            
            col_details = []
            for col in columns:
                col_type = str(col['type'])
                is_pk = col.get('primary_key', False)
                pk_str = " PRIMARY KEY" if is_pk else ""
                col_details.append(f"{col['name']} {col_type}{pk_str}")
                
            schema_info[table] = {
                "columns": [c['name'] for c in columns],
                "detailed_columns": col_details,
                "foreign_keys": [
                    f"{fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}"
                    for fk in fks
                ]
            }
        return schema_info
    except Exception as e:
        logger.error(f"Error inspecting DB schema: {e}")
        return {}

def format_schema_for_prompt() -> str:
    """Formats DB schema into DDL-like text for AI LLM prompts."""
    schema_dict = inspect_db_schema()
    if not schema_dict:
        # Fallback schema representation if DB is initializing
        return """
CREATE TABLE students (student_id INT PRIMARY KEY, first_name VARCHAR, last_name VARCHAR, email VARCHAR, department_id INT, cgpa DECIMAL, enrollment_year INT);
CREATE TABLE courses (course_id INT PRIMARY KEY, course_code VARCHAR, course_title VARCHAR, credits INT, department_id INT, instructor_id INT);
CREATE TABLE enrollments (enrollment_id INT PRIMARY KEY, student_id INT, course_id INT, grade VARCHAR, grade_point DECIMAL, semester VARCHAR);
CREATE TABLE departments (department_id INT PRIMARY KEY, department_name VARCHAR, building VARCHAR, budget DECIMAL);
CREATE TABLE instructors (instructor_id INT PRIMARY KEY, name VARCHAR, email VARCHAR, department_id INT, salary DECIMAL);
"""
    
    prompt_parts = []
    for table, details in schema_dict.items():
        cols_str = ", ".join(details["detailed_columns"])
        prompt_parts.append(f"CREATE TABLE {table} ({cols_str});")
    return "\n".join(prompt_parts)
