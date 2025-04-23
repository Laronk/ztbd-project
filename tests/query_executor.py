import time
from reset_db import reset_database
from log_utils import get_query_type

# Set of SQL command types that can't be rolled back in Postgres
ROLLBACK_INCOMPATIBLE = {"CREATE", "DROP", "ALTER", "VACUUM", "GRANT", "REVOKE"}

def execute_query_safely(conn, query_label, query):
    """
    # 1. It takes a database connection, a label for the query, and the SQL query itself.
    # 2. It determines the type of the query using the `get_query_type` function.
    # 3. It initializes a result dictionary to store the outcome of the query execution.
    # 4. It attempts to execute the query within a try-except block.
    # 5. If the query is rollback-incompatible, it resets the database before executing the query.
    # 6. It measures the execution time of the query.
    # 7. It executes the query using a cursor from the connection.
    # 8. It updates the result dictionary with the execution time and row count.
    # 9. If the query is successful, it rolls back the transaction if it's not rollback-incompatible.
    # 10. If an exception occurs, it updates the result dictionary with the error message and rolls back the transaction if necessary.
    # 11. Finally, it returns the result dictionary containing the query label, query, type, success status, row count, error message, and execution time.
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
        if query_type in ROLLBACK_INCOMPATIBLE:
            print(f"⚠️ Non-rollback-compatible query detected: [{query_type}] — Resetting DB...")
            reset_database(with_import=True)

        start = time.time()

        with conn.cursor() as cur:
            cur.execute(query)
            result["execution_time"] = time.time() - start
            result["rowcount"] = cur.rowcount
            result["success"] = True

            if query_type not in ROLLBACK_INCOMPATIBLE:
                conn.rollback()

    except Exception as e:
        result["execution_time"] = time.time() - start
        result["error"] = str(e)

        if query_type not in ROLLBACK_INCOMPATIBLE:
            conn.rollback()

    return result
