import psycopg2
import json
import os
import argparse
from log_utils import QueryLogger
from query_executor import execute_query_safely


def load_queries(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"❌ Query file not found at: {filepath}")
    with open(filepath, "r") as f:
        return json.load(f)


def connect_to_postgres():
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", 5432)
    dbname = os.getenv("DB_NAME", "mydb")
    user = os.getenv("DB_USER", "myuser")
    password = os.getenv("DB_PASSWORD", "mypassword")

    print(f"🔌 Connecting to PostgreSQL at {host}:{port} (db: {dbname}, user: {user})")

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )


def run_queries(test_suites, conn, logger):
    for suite_name, suite_data in test_suites.items():
        print(f"\n🔍 Running test suite: {suite_name} ({len(suite_data['queries'])} queries)")
        for item in suite_data.get("queries", []):
            result = execute_query_safely(conn, item["label"], item["query"], item.get("setup", []))
            logger.log(
                query_label=result["label"],
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

    conn = connect_to_postgres()
    logger = QueryLogger()
    logger.suites_run = list(test_suites.keys())  # <- For summary logging
    run_queries(test_suites, conn, logger)
    conn.close()
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
        default="test_postgres_queries_simple.json",
        help="Path to query suite JSON file"
    )

    args = parser.parse_args()
    run_test_suite(args.file, selected_suites=args.suites)
