# ZTBD-Projekt-PhysioNet

Repozytorium projektu realizowanego w ramach kursu **Zaawansowane Technologie Baz Danych**.  
Projekt analizuje dane z serwisu [PhysioNet](https://physionet.org/) z wykorzystaniem systemu Docker i PostgreSQL.

Aby uzyskać szczegółowe informacje na temat schematu bazy danych, zapoznaj się z oficjalną dokumentacją:
[Tabela Admission Drug - eICU Collaborative Research Database](https://eicu-crd.mit.edu/eicutables/admissiondrug/)

📄 Raport z projektu:  
[Kliknij tutaj, aby otworzyć dokument Google](https://docs.google.com/document/d/1ZmpCnKk0zSc0tX4yNQb256DEPOkSrqNnXOcXAUdnOXw/edit?usp=sharing)

---

## 🚀 Setup

Download the EICU demo dataset and place the .sqlite3 file into the `init/` folder.

Download the [eICU Collaborative Research Database Demo (v2.0.1)](https://physionet.org/static/published-projects/eicu-crd-demo/eicu-collaborative-research-database-demo-2.0.1.zip) and extract it into the `init/` folder. Only the `.sqlite3` file is required for this project.

To extract the `.zip` file on Linux and move the `.sqlite3` file to the `init/` folder, use the following commands:

```bash
wget -r -N -c -np https://physionet.org/content/eicu-crd-demo/2.0.1/sqlite/eicu_v2_0_1.sqlite3.gz
```

```bash
unzip eicu_v2_0_1.sqlite3.gz -d temp_folder
mv temp_folder/eicu_v2_0_1.sqlite3 init/
rm -r temp_folder
```

---

## 🐳 Running the Docker Environment

### 1. Build all containers

```bash
docker-compose build
```

### 2. Start the database and import the data

This starts PostgreSQL and runs `pgloader` to load data from SQLite into PostgreSQL:

```bash
docker-compose up -d postgres pgloader
```

### 3. Run tests

To execute the full test suite after data import:

```bash
docker-compose run --rm database-tester
```

You can also selectively run **specific test suites** using the `--suites` flag:

```bash
docker-compose run --rm database-tester --suites "Simple queries" "Complex queries"
```

Use a custom query file (optional):

```bash
docker-compose run --rm database-tester --file tests/my_custom_queries.json
```

📝 **Note:**  
- Test queries are defined in `test_postgres_queries.json`
- Suite names must match the keys in that file

---

## 📊 Summary Output

- After all queries are executed, a detailed **summary log** is generated.
- The summary aggregates **all suites run in the current session**, including:
  - Total queries
  - Success/failure count
  - Execution time statistics
  - Memory/CPU usage
  - System info
  - List of executed test suites

Logs and summaries are saved as:
- `query_log_<timestamp>.txt`
- `query_log_<timestamp>.summary.txt`

---

## 🧹 Cleaning Up

### Reset everything (volumes, database, logs)

```bash
docker-compose down -v
```

This wipes persistent volumes (including the PostgreSQL database).

### Total Docker cleanup (⚠️ Warning)

> ⚠️ `docker system prune` will:
> - Remove all stopped containers
> - Delete unused networks
> - Delete dangling images and build cache  
> - It may also remove volumes if not in use

Proceed with caution:

```bash
docker system prune
```

---

## 📁 Project Structure

```text
.
├── docker-compose.yml            # Compose config for DB, loader, and tester
├── Dockerfile.postgres           # PostgreSQL + pgloader setup
├── Dockerfile.tester             # Python test runner
├── init/                         # SQLite DB and import script
├── tests/                        # Python scripts and query definitions
│   ├── test_postgres.py
│   ├── test_postgres_queries.json
│   ├── query_executor.py
│   └── log_utils.py
├── docker_volumes/              # Persistent volume for PostgreSQL
└── logs/                         # Auto-generated logs after test runs
```

---

## ✅ Author Notes

This environment is designed for reproducible, performance-aware database testing using realistic medical data. Feel free to fork and adapt it to other databases or query workloads.