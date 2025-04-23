import sqlite3
import os

# === CONFIG ===
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../init/eicu_v2_0_1.sqlite3"))

# === CONNECT ===
print(f"🔍 Connecting to: {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# === TABLE LIST ===
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cur.fetchall()]
print(f"📦 Found {len(tables)} tables")

# === TARGET TYPES & DEFAULTS ===
numeric_like = ("int", "real", "numeric", "double", "decimal", "float", "smallint")
default_values = {
    "int": 0,
    "integer": 0,
    "smallint": 0,
    "bigint": 0,
    "real": 0.0,
    "float": 0.0,
    "double": 0.0,
    "double precision": 0.0,
    "numeric": 0.0,
    "decimal": 0.0
}

# === TRACKING ===
cleaning_summary = []
warnings = []

# === MAIN LOGIC ===
for table in tables:
    try:
        cur.execute(f"PRAGMA table_info({table});")
        columns = cur.fetchall()

        for col in columns:
            col_name = col[1]
            col_type = col[2].lower()
            is_not_null = col[3] == 1
            match = next((t for t in numeric_like if t in col_type), None)

            if match:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {col_name} = ''")
                    count = cur.fetchone()[0]

                    if count > 0:
                        if is_not_null:
                            default_val = default_values.get(match, 0)
                            cur.execute(
                                f"UPDATE {table} SET {col_name} = ? WHERE {col_name} = ''",
                                (default_val,)
                            )
                            cleaning_summary.append((table, col_name, count, "default", default_val))
                            warnings.append(f"{table}.{col_name} is NOT NULL — set {count} rows to default value: {default_val}")
                        else:
                            cur.execute(f"UPDATE {table} SET {col_name} = NULL WHERE {col_name} = ''")
                            cleaning_summary.append((table, col_name, count, "null", None))

                except Exception as check_err:
                    print(f"⚠️ Error checking {table}.{col_name}: {check_err}")
    except Exception as e:
        print(f"⚠️ Error reading table {table}: {e}")

# === FINALIZE ===
conn.commit()
conn.close()

# === SUMMARY ===
print("\n📋 Cleaning Summary")
if cleaning_summary:
    for table, column, count, action, default in cleaning_summary:
        if action == "default":
            print(f"  - {table}.{column}: {count} replaced with default = {default}")
        else:
            print(f"  - {table}.{column}: {count} replaced with NULL")
else:
    print("✅ No cleaning needed — all numeric fields are clean.")

if warnings:
    print("\n⚠️ Warnings (defaults used):")
    for w in warnings:
        print("  -", w)
