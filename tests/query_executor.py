import time
from reset_db import reset_database
from log_utils import get_query_type

# Set of SQL command types that can't be rolled back in Postgres
ROLLBACK_INCOMPATIBLE = {"CREATE", "DROP", "ALTER", "VACUUM", "GRANT", "REVOKE"}

def execute_query_safely(conn, query_label, query):
    """
    Executes a SQL query using the following logic:

    1. Determines the type of the query (e.g., SELECT, CREATE, etc.)
    2. If the query type is rollback-compatible:
       - Starts a transaction
       - Executes the query
       - Rolls it back to reset state
    3. If the query type is not rollback-compatible:
       - Calls reset_database() to reinitialize the DB
       - Executes the query afterward without rollback
    4. Measures and returns the execution time
    5. Captures the row count or failure details
    6. Returns a dictionary with query execution metadata
    """

    query_type = get_query_type(query)
    result = {
        "label": query_label,
        "query": query,
        "type": query_type,
        "success": False,
        "rowcount": -1,
        "error": None,
        "execution_time": 0.0,
    }

    try:
        # Reset database if the query cannot be safely rolled back
        if query_type in ROLLBACK_INCOMPATIBLE:
            print(f"⚠️ Non-rollback-compatible query detected: [{query_type}] — Resetting DB...")
            reset_database(with_import=True)

        cur = conn.cursor()

        if query_type not in ROLLBACK_INCOMPATIBLE:
            cur.execute("BEGIN;")

        start = time.time()
        cur.execute(query)
        result["execution_time"] = time.time() - start
        result["rowcount"] = cur.rowcount
        result["success"] = True

        if query_type not in ROLLBACK_INCOMPATIBLE:
            conn.rollback()
        cur.close()

    except Exception as e:
        result["execution_time"] = time.time() - start
        result["error"] = str(e)
        if query_type not in ROLLBACK_INCOMPATIBLE:
            conn.rollback()
        cur.close()

    return result
