import psycopg2
import json
import os
import argparse
from utils.QueryLogger import QueryLogger
from utils.log_utils import get_file_name_from_path, timestamp
from query_executor import execute_query_safely

from config import (
    POSTGRESQL_CONFIG
)

def load_queries(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"❌ Query file not found at: {filepath}")
    with open(filepath, "r") as f:
        return json.load(f)


def connect_to_postgres():
    host = POSTGRESQL_CONFIG["host"]
    port = POSTGRESQL_CONFIG["port"]
    dbname = POSTGRESQL_CONFIG["database"]
    user = POSTGRESQL_CONFIG["user"]
    password = POSTGRESQL_CONFIG["password"]

    print(f"🔌 Connecting to PostgreSQL at {host}:{port} (db: {dbname}, user: {user})")

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )


def run_queries(test_suites, conn_func, logger):
    for suite_name, suite_data in test_suites.items():
        print(f"\n🔍 Running test suite: {suite_name} ({len(suite_data['queries'])} queries)")
        for item in suite_data.get("queries", []):
            skip_reason = item.get("skip")
            query_label = item.get("label")
            if skip_reason:
                if isinstance(skip_reason, str) or isinstance(skip_reason, bool):
                    pass
                else:
                    print(f"skip_reason: {skip_reason}")
                    raise ValueError(
                        f"Invalid skip reason for query '{query_label}': {skip_reason}. "
                        "Must be a string detailing the skip reason or boolean."
                    )
            	
                
                msg = f"Skipping test: {query_label}"
                if isinstance(skip_reason, str):
                    msg += f" | Reason: {skip_reason}"
                print(msg)
                logger.log_skip(f"{query_label}", reason=skip_reason)

            result = execute_query_safely(conn_func, item)
            test_type = result["type"]
            if test_type.lower() == "PARALLEL".lower():
                logger.log_parallel_test(
                    query_label=result["label"],
                    query_type=result["type"],
                    query=result["query"],
                    execution_time=result["execution_time"],
                    min_time=result["min_time"],
                    max_time=result["max_time"],
                    avg_time=result["avg_time"],
                    rowcount=result["rowcount"],
                    success=result["success"],
                    setup_queries=item.get("setup", []),
                    error_message=result["error"]
                )
            else:
                logger.log_regular_test(
                    query_label=result["label"],
                    query_type=result["type"],
                    query=result["query"],
                    execution_time=result["execution_time"],
                    rowcount=result["rowcount"],
                    success=result["success"],
                    setup_queries=item.get("setup", []),
                    error_message=result["error"]
                )


def run_test_suite(queries_file, selected_suites=None):
    test_suites = load_queries(queries_file)

    # Filter suites if user specified any
    if selected_suites:
        filtered = {
            name: data for name, data in test_suites.items()
            if name in selected_suites
        }
        if not filtered:
            print(f"❌ No matching test suites found for: {selected_suites}")
            return
        test_suites = filtered

    logger = QueryLogger(
        timestamp_id=timestamp(),
        test_file_name=get_file_name_from_path(queries_file),
        selected_suites=selected_suites
    )
    logger.suites_run = list(test_suites.keys()) # <- For summary logging
    run_queries(test_suites, connect_to_postgres, logger)
    logger.finish()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run PostgreSQL query tests.")
    parser.add_argument(
        "--suites",
        nargs="+",
        help="Names of test suites to run (default: all)"
    )
    parser.add_argument(
        "--file",
        help="Path to query suite JSON file"
    )

    args = parser.parse_args()
    run_test_suite(args.file, selected_suites=args.suites)
