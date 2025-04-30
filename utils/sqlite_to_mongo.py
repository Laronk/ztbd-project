import sqlite3
import os
import json

# === CONFIG ===
SQLITE_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../init/eicu_v2_0_1.sqlite3"))
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../init/eicu_json"))

os.makedirs(OUTPUT_DIR, exist_ok=True)

def export_tables_to_json_files():
    if not os.path.exists(SQLITE_DB_PATH):
        raise FileNotFoundError(f"SQLite file not found at: {SQLITE_DB_PATH}")

    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row["name"] for row in cursor.fetchall()]

    for table in tables:
        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()
        table_data = [dict(row) for row in rows]

        table_path = os.path.join(OUTPUT_DIR, f"{table}.json")
        with open(table_path, "w", encoding="utf-8") as f:
            json.dump(table_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Saved {len(rows)} rows from table '{table}' to '{table_path}'")

    conn.close()
    print(f"\n🎉 All tables dumped into JSON files in: {OUTPUT_DIR}")

if __name__ == "__main__":
    export_tables_to_json_files()
