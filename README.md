
# ZTBD-Projekt-PhysioNet

Repozytorium projektu realizowanego w ramach kursu **Zaawansowane Technologie Baz Danych**.  
Projekt analizuje dane z serwisu [PhysioNet](https://physionet.org/) z wykorzystaniem systemu Docker i PostgreSQL.

Aby uzyskać szczegółowe informacje na temat schematu bazy danych, zapoznaj się z oficjalną dokumentacją:  
[Tabela Admission Drug - eICU Collaborative Research Database](https://eicu-crd.mit.edu/eicutables/admissiondrug/)

📄 Raport z projektu:  
[Kliknij tutaj, aby otworzyć dokument Google](https://docs.google.com/document/d/1ZmpCnKk0zSc0tX4yNQb256DEPOkSrqNnXOcXAUdnOXw/edit?usp=sharing)

---

## 🚀 Setup

Download the EICU demo dataset and place the `.sqlite3` file into the `init/` folder.

Download the [eICU Collaborative Research Database Demo (v2.0.1)](https://physionet.org/static/published-projects/eicu-crd-demo/eicu-collaborative-research-database-demo-2.0.1.zip) and extract it into the `init/` folder. Only the `.sqlite3` file is required for this project.

To extract the `.gz` file on Linux and move the `.sqlite3` file:

```bash
wget -r -N -c -np https://physionet.org/content/eicu-crd-demo/2.0.1/sqlite/eicu_v2_0_1.sqlite3.gz
gunzip eicu_v2_0_1.sqlite3.gz
mv eicu_v2_0_1.sqlite3 init/
```

---

## 🧼 1. Pre-clean the SQLite database (**required before import**)

Before importing the dataset into PostgreSQL, you must clean invalid values that would cause type errors during the import process.

Run the cleaning script:

```bash
python3 utils/preclean_all.py
```

This script:
- Replaces `""` with `NULL` in nullable numeric fields
- Replaces `""` with safe defaults (like `0`) in `NOT NULL` numeric fields
- Prints a summary of all changes and affected columns

> ⚠️ **This step is mandatory.** PostgreSQL is strict about types, and without pre-cleaning, the import will fail.

---

## 🧼 2. Convert SQLite to JSON (required for MongoDB import)

If you want to test using MongoDB, convert the `.sqlite3` file to JSON format first:

```bash
python3 utils/sqlite_to_json.py
```

This script exports all tables and rows to a structured `.json` file.  
It is required for MongoDB import or testing.

---

## 🐳 3. Build and Run the Docker Environment

### Build all containers

```bash
docker-compose build
```

### Start the database and import the data

This starts PostgreSQL and runs `pgloader` to load data from SQLite into PostgreSQL:

```bash
docker-compose up -d postgres pgloader
```

---

## 🧪 4. Run the Test Suite

To execute the full test suite after data import:

```bash
docker-compose run --rm database-tester
```

You can also selectively run **specific test suites**:

```bash
docker-compose run --rm database-tester --suites "Simple queries" "Complex queries"
```

To use a custom query file:

```bash
docker-compose run --rm database-tester --file tests/my_custom_queries.json
```

📝 **Note:**
- Test queries are defined in `test_postgres_queries.json`
- Suite names must match the keys in that file

---

## 📊 Summary Output

After all queries are executed, detailed logs are generated including:

- Total queries run
- Execution time stats (avg, fastest, slowest)
- CPU and memory usage
- Number of failed queries
- List of executed test suites

Logs are saved as:
- `querylog_<timestamp>.txt`
- `querylog_<timestamp>.summary.txt`

---

## 🧹 Cleaning Up

### Reset everything (volumes, database, logs)

```bash
docker-compose down -v
```

This removes the PostgreSQL data volume and any test results.

### Total Docker cleanup (⚠️ DANGEROUS)

```bash
docker system prune
```

> ⚠️ This deletes unused containers, networks, and build cache.

---

## 📁 Project Structure

```text
.
├── docker-compose.yml            # Compose config for DB, loader, and tester
├── Dockerfile.postgres           # PostgreSQL + pgloader setup
├── Dockerfile.tester             # Python test runner
├── init/                         # SQLite DB and import script
│   └── eicu_v2_0_1.sqlite3       # eICU demo database (required)
├── utils/                        # Pre-cleaning scripts
│   └── preclean_all.py           # Smart DB cleaner
│   └── sqlite_to_mongo.py           # mongo DB converter
├── tests/                        # Python scripts and query definitions
│   ├── test_postgres.py
│   ├── test_postgres_queries.json
│   ├── query_executor.py
│   └── log_utils.py
├── docker_volumes/               # Persistent volume for PostgreSQL
└── logs/                         # Auto-generated logs after test runs
```

---

## ✅ Author Notes

This environment is designed for reproducible, performance-aware database testing using realistic medical data.  
Feel free to fork and adapt it to other databases or query workloads.
