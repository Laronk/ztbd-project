import os

MAX_PARALLEL_QUERIES = 20

ROLLBACK_INCOMPATIBLE = {"CREATE", "DROP", "ALTER", "VACUUM", "GRANT", "REVOKE"}
PARALLEL_EXECUTION_ALLOWED = {"SELECT", "INSERT", "UPDATE", "DELETE"}

POSTGRESQL_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", 5432),
    "database": os.getenv("DB_NAME", "mydb"),
    "user": os.getenv("DB_USER", "myuser"),
    "password": os.getenv("DB_PASSWORD", "mypassword"),
}