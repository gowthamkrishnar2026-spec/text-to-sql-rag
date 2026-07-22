import pytest
from app.services.sql_validator import sanitize_and_validate_sql, SQLValidationError

def test_valid_select_query():
    sql = "SELECT student_id, first_name, cgpa FROM students WHERE cgpa > 8.0;"
    result = sanitize_and_validate_sql(sql)
    assert "SELECT" in result
    assert result.endswith(";")

def test_valid_with_cte_query():
    sql = "WITH top_students AS (SELECT * FROM students WHERE cgpa > 9.0) SELECT * FROM top_students;"
    result = sanitize_and_validate_sql(sql)
    assert result.startswith("WITH")

def test_reject_drop_table():
    sql = "DROP TABLE students;"
    with pytest.raises(SQLValidationError) as exc_info:
        sanitize_and_validate_sql(sql)
    assert "Forbidden" in str(exc_info.value)

def test_reject_delete_from():
    sql = "DELETE FROM students WHERE student_id = 1;"
    with pytest.raises(SQLValidationError) as exc_info:
        sanitize_and_validate_sql(sql)
    assert "Forbidden" in str(exc_info.value)

def test_reject_update():
    sql = "UPDATE students SET cgpa = 10.0 WHERE student_id = 1;"
    with pytest.raises(SQLValidationError) as exc_info:
        sanitize_and_validate_sql(sql)
    assert "Forbidden" in str(exc_info.value)

def test_reject_multiple_statements():
    sql = "SELECT * FROM students; DROP TABLE courses;"
    with pytest.raises(SQLValidationError) as exc_info:
        sanitize_and_validate_sql(sql)
    assert "Multiple SQL statements" in str(exc_info.value) or "Forbidden" in str(exc_info.value)

def test_reject_truncate():
    sql = "TRUNCATE TABLE enrollments;"
    with pytest.raises(SQLValidationError) as exc_info:
        sanitize_and_validate_sql(sql)
    assert "Forbidden" in str(exc_info.value)
