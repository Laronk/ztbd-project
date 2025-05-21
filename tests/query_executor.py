import time
import statistics
import threading
from reset_db import reset_database
from log_utils import get_query_type
from validators import validate_simulated_client_number, validate_queries_per_time, validate_execution_loop_time_ms

from config import (
    ROLLBACK_INCOMPATIBLE,
    PARALLEL_EXECUTION_ALLOWED,
)


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


def run_parallel_setup(setup, conn_func):
    for q in setup or []:
        if get_query_type(q) in ROLLBACK_INCOMPATIBLE:
            return False, f"Disallowed query type '{get_query_type(q)}' in setup phase"

    try:
        conn = conn_func()
        with conn.cursor() as cur:
            for q in setup:
                cur.execute(q)
        conn.commit()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


def parallel_client_worker(client_id, query_seq, queries_per_time, execution_loop_time_ms, conn_func, result_list, lock):
    conn = conn_func()
    try:
        for _ in range(queries_per_time):
            start = time.time()
            with conn.cursor() as cur:
                for q in query_seq:
                    cur.execute(q)
            elapsed = time.time() - start

            with lock:
                result_list.append(elapsed)

            time.sleep(execution_loop_time_ms / 1000.0)
    except Exception as e:
        with lock:
            result_list.append(f"ERROR: {str(e)}")
    finally:
        conn.close()


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

    # Validate fields
    for validator, value in [
        (validate_simulated_client_number, simulated_client_number),
        (validate_queries_per_time, queries_per_time),
        (validate_execution_loop_time_ms, execution_loop_time),
    ]:
        ok, err = validator(value)
        if not ok:
            return {
                "label": query_label,
                "query": "[PARALLEL]",
                "type": "PARALLEL",
                "success": False,
                "error": f"❌ {err}",
                "rowcount": -1,
                "execution_time": 0.0,
            }

    # Check for disallowed operations
    for q in query_seq:
        qtype = get_query_type(q)
        if qtype not in PARALLEL_EXECUTION_ALLOWED:
            return {
                "label": query_label,
                "query": "[PARALLEL]",
                "type": "PARALLEL",
                "success": False,
                "error": f"❌ Query type '{qtype}' not allowed in parallel execution",
                "rowcount": -1,
                "execution_time": 0.0,
            }

    # Setup phase
    ok, setup_error = run_parallel_setup(setup, conn_func)
    if not ok:
        return {
            "label": query_label,
            "query": "[PARALLEL]",
            "type": "PARALLEL",
            "success": False,
            "error": f"❌ Setup failed: {setup_error}",
            "rowcount": -1,
            "execution_time": 0.0,
        }

    # Parallel execution
    lock = threading.Lock()
    results = []
    threads = []

    for i in range(simulated_client_number):
        t = threading.Thread(
            target=parallel_client_worker,
            args=(i, query_seq, queries_per_time, execution_loop_time, conn_func, results, lock)
        )
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # Split durations vs errors
    durations = [x for x in results if isinstance(x, float)]
    errors = [x for x in results if isinstance(x, str)]

    return {
        "label": query_label,
        "query": "[PARALLEL]",
        "type": "PARALLEL",
        "success": len(errors) == 0,
        "error": errors if errors else None,
        "rowcount": len(durations),
        "execution_time": sum(durations),
        "min_time": min(durations) if durations else None,
        "max_time": max(durations) if durations else None,
        "avg_time": statistics.mean(durations) if durations else None,
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
