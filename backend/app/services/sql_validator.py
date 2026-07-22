import re
import sqlparse

FORBIDDEN_KEYWORDS = {
    "DROP", "DELETE", "UPDATE", "ALTER", "TRUNCATE", "INSERT", 
    "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "PG_SLEEP", 
    "COPY", "VACUUM", "REINDEX", "SHUTDOWN"
}

class SQLValidationError(Exception):
    """Exception raised when an generated or user-provided SQL fails security validation."""
    pass

def sanitize_and_validate_sql(sql_query: str) -> str:
    """
    Cleans and validates a SQL query string.
    Only permits safe read-only SELECT or WITH ... SELECT queries.
    Raises SQLValidationError if unsafe patterns or destructive commands are detected.
    """
    if not sql_query or not sql_query.strip():
        raise SQLValidationError("SQL query string is empty.")

    # 1. Clean markdown code fences if present (```sql ... ```)
    clean_sql = re.sub(r"```(?:sql)?", "", sql_query, flags=re.IGNORECASE).strip()
    clean_sql = clean_sql.rstrip("`").strip()

    # 2. Remove SQL comments to avoid hiding forbidden statements
    parsed_statements = sqlparse.parse(clean_sql)
    if not parsed_statements:
        raise SQLValidationError("Invalid SQL syntax: could not parse query.")
    
    # 3. Disallow multiple statements (semicolon injection)
    non_empty_statements = [s for s in parsed_statements if s.get_type() != 'UNKNOWN' or s.value.strip()]
    if len(non_empty_statements) > 1:
        # Check if statements are just trailing semicolons
        actual_statements = [s for s in non_empty_statements if re.search(r'\w+', s.value)]
        if len(actual_statements) > 1:
            raise SQLValidationError("Security Warning: Multiple SQL statements are not allowed.")

    statement = non_empty_statements[0]
    
    # 4. Enforce query type: Must be SELECT or WITH
    stmt_type = statement.get_type().upper()
    raw_str = statement.value.strip()

    first_word_match = re.match(r"^\s*([a-zA-Z]+)", raw_str)
    first_word = first_word_match.group(1).upper() if first_word_match else ""

    if stmt_type not in ["SELECT", "UNKNOWN"] and first_word not in ["SELECT", "WITH"]:
        raise SQLValidationError(f"Forbidden statement type '{first_word}'. Only SELECT queries are permitted.")

    if not (first_word == "SELECT" or first_word == "WITH"):
        raise SQLValidationError("Security Warning: Query must begin with SELECT or WITH.")

    # 5. Check for forbidden keywords across all tokens
    tokens = [token.value.upper() for token in statement.flatten()]
    for token in tokens:
        # Match exact forbidden word
        words = re.findall(r"\b[A-Z_]+\b", token)
        for w in words:
            if w in FORBIDDEN_KEYWORDS:
                raise SQLValidationError(f"Forbidden SQL operation detected: '{w}'. Only read-only SELECT queries are allowed.")

    # Normalize trailing semicolon
    final_sql = raw_str.rstrip(";") + ";"
    return final_sql
