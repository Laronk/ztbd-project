import time
from reset_db import reset_database
from log_utils import get_query_type

ROLLBACK_INCOMPATIBLE = {"CREATE", "DROP", "ALTER", "VACUUM", "GRANT", "REVOKE"}


def is_rollback_safe(queries):
    return all(get_query_type(q) not in ROLLBACK_INCOMPATIBLE for q in queries)

def execute_single_query(conn_func, query_label, query, setup):
    conn = conn_func()
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

    all_queries = setup + [query]
    rollback_safe = is_rollback_safe(all_queries)

    try:
        if not rollback_safe:
            print(f"⚠️ Detected non-transaction-safe operation(s) — will reset DB after test.")

        start = time.time()

        if rollback_safe:
            with conn.cursor() as cur:
                cur.execute("BEGIN;")
                for setup_query in setup:
                    cur.execute(setup_query)
                cur.execute(query)
                result["execution_time"] = time.time() - start
                result["rowcount"] = cur.rowcount
                result["success"] = True
                conn.rollback()
        else:
            cur = conn.cursor()
            for setup_query in setup:
                cur.execute(setup_query)
            cur.execute(query)
            result["execution_time"] = time.time() - start
            result["rowcount"] = cur.rowcount
            result["success"] = True
            cur.close()
            reset_database(with_import=True)

        # close the connection
        conn.close()
    except Exception as e:
        conn.close()
        result["execution_time"] = time.time() - start
        result["error"] = str(e)

        if rollback_safe:
            conn.rollback()
        else:
            reset_database(with_import=True)

    return result


def execute_parallel_query(
    conn_func,
    query_label,
    query_seq,
    simulated_client_number=2,
    queries_per_time=1,
    execution_loop_time=1000,
    setup=None
):
    print(f"Executing parallel query: {query_label}")
    print(f"Clients: {simulated_client_number}, QPT: {queries_per_time}, Interval: {execution_loop_time} ms")
    print(f"Setup queries: {len(setup or [])}, Query sequence: {len(query_seq)} queries")

    # Placeholder — will implement threading and execution loop in the next step
    # conn.close()
    return {
        "label": query_label,
        "query": "[PARALLEL]",
        "type": "PARALLEL",
        "success": True,
        "rowcount": -1,
        "error": None,
        "execution_time": 0.0,
    }


def execute_query_safely(conn_func, query):
    if query.get("run_parallel"):
        return execute_parallel_query(
            conn_func,
            query_label=query["label"],
            query_seq=query.get("query_seq", []),
            simulated_client_number=query.get("simulated_client_number", 2),
            queries_per_time=query.get("queries_per_time", 1),
            execution_loop_time=query.get("execution_loop_time_ms", 1000),
            setup=query.get("setup", [])
        )
    return execute_single_query(conn_func, query["label"], query["query"], query.get("setup", []))
