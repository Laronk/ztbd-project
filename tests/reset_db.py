import psycopg2
import subprocess
import os

# Configuration – ideally match your docker-compose environment
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", 5432)
DB_NAME = os.getenv("DB_NAME", "mydb")
DB_USER = os.getenv("DB_USER", "myuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "mypassword")

PGLOADER_SQLITE_PATH = "/init/eicu_v2_0_1.sqlite3"
PGLOADER_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def reset_postgres_schema():
    """Drop and recreate the public schema in the database."""
    print("🧹 Dropping and recreating public schema...")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA public CASCADE;")
        cur.execute("CREATE SCHEMA public;")
    conn.close()
    print("✅ Schema reset complete.")

def reimport_sqlite_data():
    """Re-import data from SQLite using pgloader."""
    print(f"📥 Re-importing data from SQLite ({PGLOADER_SQLITE_PATH}) to PostgreSQL...")
    result = subprocess.run(
        ["pgloader", PGLOADER_SQLITE_PATH, PGLOADER_URL],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if result.returncode != 0:
        print("❌ pgloader import failed:")
        print(result.stderr.decode())
        raise RuntimeError("pgloader import failed")

    print("✅ pgloader import complete.")

def reset_database(with_import=True):
    """Reset the DB and optionally re-import SQLite data."""
    reset_postgres_schema()
    if with_import:
        reimport_sqlite_data()

# Allow CLI use
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Reset PostgreSQL database and optionally reimport SQLite data.")
    parser.add_argument("--no-import", action="store_true", help="Skip the SQLite import step")
    args = parser.parse_args()

    reset_database(with_import=not args.no_import)
