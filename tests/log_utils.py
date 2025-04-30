import os
import time
import psutil
from datetime import datetime
from collections import defaultdict
import statistics

LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

import platform
import psutil

def get_system_info():
    cpu_info = platform.processor()
    cpu_count = psutil.cpu_count(logical=True)
    memory_total_gb = round(psutil.virtual_memory().total / (1024**3), 2)

    return {
        "CPU": cpu_info,
        "CPU_CORES": cpu_count,
        "TOTAL_MEMORY_GB": memory_total_gb
    }

def get_log_filename(prefix="querylog_", ext=".txt"):
    dt_str = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(LOG_DIR, f"{prefix}{dt_str}{ext}")

def timestamp():
    return datetime.utcnow().isoformat() + "Z"

def get_query_type(query):
    return query.strip().split()[0].upper()

class QueryLogger:
    def __init__(self, log_file=None):
        self.suites_run = []
        self.log_file = log_file or get_log_filename()
        self.start_time = time.time()
        self.query_count = 0
        self.fail_count = 0
        self.total_exec_time = 0.0
        self.execution_times = []
        self.cpu_usages = []
        self.memory_usages = []
        self.by_type = defaultdict(list)
        self.process = psutil.Process(os.getpid())
        self._init_log()

    def _init_log(self):
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(f"--- Query Benchmark Log ({timestamp()}) ---\n\n")

    def log(self, query_label, query, execution_time, rowcount, success=True, setup_queries=[], error_message=None):
        self.query_count += 1
        self.total_exec_time += execution_time
        self.execution_times.append(execution_time)
        if not success:
            self.fail_count += 1

        query_type = get_query_type(query)
        self.by_type[query_type].append(execution_time)

        cpu_pct = self.process.cpu_percent(interval=0.1)
        mem_rss_mb = self.process.memory_info().rss / (1024 * 1024)

        self.cpu_usages.append(cpu_pct)
        self.memory_usages.append(mem_rss_mb)

        # Ordered log format:
        log_line = (
            f"{timestamp()} | [{query_type}] | SUCCESS: {success} | QUERY_NAME: {query_label} | "
            f"EXEC_TIME: {round(execution_time, 4)}s | ROWS: {rowcount} | "
            f"CPU: {round(cpu_pct, 2)}% | MEM: {round(mem_rss_mb, 2)}MB | QUERY: {query.strip()};"
        )

        if setup_queries:
            setup_types = [get_query_type(q) for q in setup_queries]
            setup_count = len(setup_queries)

            # Count each type for this specific test only
            setup_type_counts = defaultdict(int)
            for stype in setup_types:
                setup_type_counts[stype] += 1

            setup_type_summary = ', '.join(f'{k}: {v}' for k, v in setup_type_counts.items())
            log_line += f" | SETUP: {setup_count} query(ies), types: {setup_type_summary}"

        if not success and error_message:
            log_line += f"  <-- ERROR: {error_message}"

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")

    def finish(self):
        import statistics
        import time

        duration = time.time() - self.start_time
        avg_time = self.total_exec_time / self.query_count if self.query_count else 0
        slowest = max(self.execution_times) if self.execution_times else 0
        fastest = min(self.execution_times) if self.execution_times else 0

        median_by_type = {
            qtype: statistics.median(times)
            for qtype, times in self.by_type.items()
        }

        sys_info = get_system_info()

        summary = (
            "\n--- System Info ---\n"
            f"CPU: {sys_info['CPU']}\n"
            f"CPU Cores: {sys_info['CPU_CORES']}\n"
            f"Total System Memory: {sys_info['TOTAL_MEMORY_GB']} GB\n"
            "\n--- Total Summary ---\n"
            f"Timestamp: {timestamp()}\n"
            f"Suites Run: {', '.join(self.suites_run)}\n"
            f"Total Queries Run: {self.query_count}\n"
            f"Total Test Suite Time: {duration:.6f} sec\n"
            f"Total Query Time (cumulative): {self.total_exec_time:.6f} sec\n"
            f"Average Query Time: {avg_time:.6f} sec\n"
            f"Fastest Query Time: {fastest:.6f} sec\n"
            f"Slowest Query Time: {slowest:.6f} sec\n"
            f"Failed Queries: {self.fail_count}\n"
            f"Median Time by Query Type: { {k: round(v, 6) for k, v in median_by_type.items()} }\n"
            f"Average CPU Usage: {sum(self.cpu_usages) / len(self.cpu_usages):.6f}%\n"
            f"Peak Memory Usage: {max(self.memory_usages):.6f} MB\n"
        )

        # Write to main log file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(summary)

        # Write to separate summary file
        summary_file = self.log_file.replace(".txt", ".summary.txt")
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(summary)

        print(summary)
        return self.log_file
