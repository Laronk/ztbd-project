import time
from reset_db import reset_database
from log_utils import get_query_type

ROLLBACK_INCOMPATIBLE = {"CREATE", "DROP", "ALTER", "VACUUM", "GRANT", "REVOKE"}

def is_rollback_safe(queries):
    return all(get_query_type(q) not in ROLLBACK_INCOMPATIBLE for q in queries)

def execute_query_safely(conn, query_label, query, setup=None):
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

    all_queries = (setup or []) + [query]
    rollback_safe = is_rollback_safe(all_queries)

    try:
        if not rollback_safe:
            print(f"⚠️ Detected non-transaction-safe operation(s) — will reset DB after test.")

        start = time.time()

        if rollback_safe:
            with conn.cursor() as cur:
                cur.execute("BEGIN;")

                if setup:
                    for setup_query in setup:
                        cur.execute(setup_query)

                cur.execute(query)
                result["execution_time"] = time.time() - start
                result["rowcount"] = cur.rowcount
                result["success"] = True

                conn.rollback()

        else:
            cur = conn.cursor()

            if setup:
                for setup_query in setup:
                    cur.execute(setup_query)

            cur.execute(query)
            result["execution_time"] = time.time() - start
            result["rowcount"] = cur.rowcount
            result["success"] = True
            cur.close()

            reset_database(with_import=True)

    except Exception as e:
        result["execution_time"] = time.time() - start
        result["error"] = str(e)

        if rollback_safe:
            conn.rollback()

        if not rollback_safe:
            reset_database(with_import=True)

    return result
