import os
import re
import time
import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.services.prompt_builder import format_schema_ddl
from app.services.schema_hints import annotate_schema, collect_value_hints, load_descriptions

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema cache — refreshed at most once every 60 seconds so the DB is not
# re-inspected on every single API request.
# ---------------------------------------------------------------------------
_schema_cache: dict = {}
_schema_cache_ts: float = 0.0
_SCHEMA_CACHE_TTL: float = 60.0  # seconds


def initialize_engine():
    """
    Attempts to connect to PostgreSQL engine. If PostgreSQL is offline or unreachable,
    gracefully initializes a local SQLite database populated with the project's init schema.
    """
    try:
        eng = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        with eng.connect() as conn:
            conn.execute(text("SELECT 1;"))
        logger.info("Successfully connected to PostgreSQL database.")
        return eng
    except Exception as e:
        logger.warning(f"PostgreSQL connection unavailable ({e}). Initializing SQLite database engine.")
        db_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../text2sql.db"))
        eng = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})

        # Populate schema if missing
        try:
            inspector = inspect(eng)
            tables = inspector.get_table_names()
            if not tables:
                _seed_sqlite_db(eng)
        except Exception as seed_err:
            logger.error(f"Error seeding SQLite database: {seed_err}")
            _seed_sqlite_db(eng)

        return eng


def _seed_sqlite_db(engine_obj):
    """Populates SQLite database from init.sql with PostgreSQL-to-SQLite DDL conversions."""
    init_sql_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../database/init.sql"))
    if not os.path.exists(init_sql_path):
        return

    with open(init_sql_path, "r") as f:
        sql_script = f.read()

    # Convert PostgreSQL specific syntax to SQLite compatible DDL
    sql_script = re.sub(r"\bSERIAL PRIMARY KEY\b", "INTEGER PRIMARY KEY AUTOINCREMENT", sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r"\bSERIAL\b", "INTEGER", sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r"\bDECIMAL\(\d+,\s*\d+\)", "REAL", sql_script, flags=re.IGNORECASE)
    sql_script = re.sub(r"\bON CONFLICT DO NOTHING\b", "", flags=re.IGNORECASE, string=sql_script)
    sql_script = re.sub(r"\bINSERT INTO\b", "INSERT OR IGNORE INTO", sql_script, flags=re.IGNORECASE)
    # SQLite doesn't support CURRENT_TIMESTAMP default on INTEGER cols — strip CHECK constraints
    sql_script = re.sub(r"CHECK\s*\([^)]*\)", "", sql_script, flags=re.IGNORECASE)

    statements = sql_script.split(";")
    with engine_obj.connect() as conn:
        for stmt in statements:
            stmt_clean = stmt.strip()
            if stmt_clean:
                try:
                    conn.execute(text(stmt_clean))
                except Exception as ex:
                    logger.debug(f"SQLite init statement warning: {ex}")
        conn.commit()


engine = initialize_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def inspect_db_schema() -> dict:
    """
    Reflects the database schema (tables, columns, types, foreign keys).
    Results are cached for _SCHEMA_CACHE_TTL seconds to avoid per-request
    DB round-trips.
    """
    global _schema_cache, _schema_cache_ts
    now = time.monotonic()
    if _schema_cache and (now - _schema_cache_ts) < _SCHEMA_CACHE_TTL:
        return _schema_cache

    try:
        inspector = inspect(engine)
        schema_info = {}
        # Exclude the internal history table from schema exposed to LLM
        excluded = {"query_history"}
        tables = [t for t in inspector.get_table_names() if t not in excluded]

        for table in tables:
            columns = inspector.get_columns(table)
            fks = inspector.get_foreign_keys(table)
            try:
                pk_cols = list(inspector.get_pk_constraint(table).get("constrained_columns") or [])
            except Exception:
                pk_cols = []

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
                ],
                # Structured key info, used by the prompt formatter and by RAG table expansion
                "primary_keys": pk_cols,
                "foreign_keys_struct": [
                    {
                        "columns": list(fk["constrained_columns"]),
                        "ref_table": fk["referred_table"],
                        "ref_columns": list(fk["referred_columns"]),
                    }
                    for fk in fks
                ],
            }

        _schema_cache = schema_info
        _schema_cache_ts = now
        return schema_info
    except Exception as e:
        logger.error(f"Error inspecting DB schema: {e}")
        return {}


_hints_cache: dict = {}
_hints_cache_ts: float = 0.0
_HINTS_CACHE_TTL: float = 300.0  # seconds


def _fetch_rows(sql: str):
    with engine.connect() as conn:
        return conn.execute(text(sql)).fetchall()


def get_prompt_schema() -> dict:
    """
    Schema for the prompt: inspect_db_schema() plus table descriptions and the allowed values of
    small-choice text columns (settings SCHEMA_DESCRIPTIONS / SCHEMA_VALUE_HINTS). The /schema
    endpoint keeps using the plain inspect_db_schema(). Falls back to the plain schema on any problem.
    """
    global _hints_cache, _hints_cache_ts
    schema = inspect_db_schema()
    if not schema:
        return schema
    try:
        descriptions = load_descriptions() if getattr(settings, "SCHEMA_DESCRIPTIONS", True) else None
        hints = None
        if getattr(settings, "SCHEMA_VALUE_HINTS", True):
            now = time.monotonic()
            if not _hints_cache or (now - _hints_cache_ts) > _HINTS_CACHE_TTL:
                _hints_cache = collect_value_hints(
                    schema, _fetch_rows, max_values=int(getattr(settings, "SCHEMA_HINT_MAX_VALUES", 12)),
                    quote=engine.dialect.identifier_preparer.quote)
                _hints_cache_ts = now
            hints = _hints_cache
        return annotate_schema(schema, descriptions, hints)
    except Exception as exc:
        logger.warning("Schema hints unavailable, using the plain schema: %s", exc)
        return schema


def format_schema_for_prompt() -> str:
    """Formats DB schema into DDL-like text for AI LLM prompts."""
    schema_dict = get_prompt_schema()
    if not schema_dict:
        return """
CREATE TABLE students (student_id INT PRIMARY KEY, first_name VARCHAR, last_name VARCHAR, email VARCHAR, department_id INT, cgpa DECIMAL, enrollment_year INT);
CREATE TABLE courses (course_id INT PRIMARY KEY, course_code VARCHAR, course_title VARCHAR, credits INT, department_id INT, instructor_id INT);
CREATE TABLE enrollments (enrollment_id INT PRIMARY KEY, student_id INT, course_id INT, grade VARCHAR, grade_point DECIMAL, semester VARCHAR);
CREATE TABLE departments (department_id INT PRIMARY KEY, department_name VARCHAR, building VARCHAR, budget DECIMAL);
CREATE TABLE instructors (instructor_id INT PRIMARY KEY, name VARCHAR, email VARCHAR, department_id INT, salary DECIMAL);
CREATE TABLE customers (customer_id INT PRIMARY KEY, customer_name VARCHAR, city VARCHAR, country VARCHAR);
CREATE TABLE products (product_id INT PRIMARY KEY, product_name VARCHAR, category VARCHAR, unit_price DECIMAL, stock_quantity INT);
CREATE TABLE orders (order_id INT PRIMARY KEY, customer_id INT, order_date DATE, total_amount DECIMAL, status VARCHAR);
CREATE TABLE order_items (item_id INT PRIMARY KEY, order_id INT, product_id INT, quantity INT, price_per_unit DECIMAL);
CREATE TABLE corp_departments (dept_id INT PRIMARY KEY, dept_name VARCHAR, location VARCHAR);
CREATE TABLE employees (emp_id INT PRIMARY KEY, emp_name VARCHAR, job_title VARCHAR, dept_id INT, hire_date DATE, salary DECIMAL);
"""

    include_keys = getattr(settings, "SCHEMA_INCLUDE_KEYS", True)
    return format_schema_ddl(schema_dict, include_keys=include_keys)
