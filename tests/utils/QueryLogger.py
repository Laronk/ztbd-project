from collections import defaultdict
import os
import time
import psutil
from .log_utils import get_query_type, get_system_info, timestamp, get_log_filename


class QueryLogger:
    def __init__(self, timestamp_id: str, test_file_name: str, selected_suites: str, log_file=None):
        # test identifier
        self.log_file_id = timestamp_id
        self.test_file_name = test_file_name
        self.selected_suites = selected_suites
        # collected data
        self.skipped_test_count = 0
        self.run_tests_count = 0
        self.suites_run = []
        self.log_file = log_file or get_log_filename()
        self.start_time = time.time()
        self.fail_count = 0
        self.total_exec_time = 0.0
        self.regualar_execution_times = []
        self.parallel_execution_stats = []
        self.cpu_usages = []
        self.memory_usages = []
        self.by_type = defaultdict(list)
        self.process = psutil.Process(os.getpid())
        self._init_log()

    def _init_log(self):
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(f"Run Test Time ID: {self.log_file_id}\n")
            f.write(f"Test File Name: {self.test_file_name}\n")
            f.write(f"Selected Suites: {', '.join(self.selected_suites)}\n")
            f.write(f"--- Test Query Log ---\n\n")

    def _collect_resource_usage(self):
        cpu_pct = self.process.cpu_percent(interval=0.1)
        mem_rss_mb = self.process.memory_info().rss / (1024 * 1024)
        self.cpu_usages.append(cpu_pct)
        self.memory_usages.append(mem_rss_mb)
        return cpu_pct, mem_rss_mb

    def _write_log_line(self, line):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def record_parallel_metrics(self, execution_time, min_time, max_time, avg_time, success):
        self.run_tests_count += 1
        self.total_exec_time += execution_time
        self.parallel_execution_stats.append((execution_time, min_time, max_time, avg_time))
        if not success:
            self.fail_count += 1

    def format_parallel_log_line(self, query_label, query_type, query, execution_time, min_time, max_time, avg_time, rowcount, success, setup_queries, error_message):
        cpu_pct, mem_rss_mb = self._collect_resource_usage()

        line = (
            f"{timestamp()} | _{query_type.upper()}_ | SUCCESS: {success} | QUERY_NAME: {query_label} | "
            f"EXEC_TOTAL_TIME: {round(execution_time, 4)}s | EXEC_MIN_TIME: {round(min_time, 4)}s | "
            f"EXEC_MAX_TIME: {round(max_time, 4)}s | EXEC_AVG_TIME: {round(avg_time, 4)}s | ROWS: {rowcount} | "
            f"CPU: {round(cpu_pct, 2)}% | MEM: {round(mem_rss_mb, 2)}MB | QUERY: {query.strip()}"
        )

        if setup_queries:
            setup_counts = defaultdict(int)
            for q in setup_queries:
                setup_counts[get_query_type(q)] += 1
            setup_summary = ', '.join(f"{k}: {v}" for k, v in setup_counts.items())
            line += f" | SETUP: {len(setup_queries)} query(ies), types: {setup_summary}"

        if not success and error_message:
            line += f"  <-- ERROR: {error_message}"

        return line

    def log_parallel_test(self, *args, **kwargs):
        self.record_parallel_metrics(
            kwargs["execution_time"], kwargs["min_time"], kwargs["max_time"],
            kwargs["avg_time"], kwargs["success"]
        )
        log_line = self.format_parallel_log_line(*args, **kwargs)
        self._write_log_line(log_line)

    def record_regular_metrics(self, execution_time, query_type, success):
        self.run_tests_count += 1
        self.total_exec_time += execution_time
        self.regualar_execution_times.append(execution_time)
        self.by_type[query_type].append(execution_time)
        if not success:
            self.fail_count += 1

    def format_regular_log_line(self, query_label, query_type, query, execution_time, rowcount, success, setup_queries, error_message):
        cpu_pct, mem_rss_mb = self._collect_resource_usage()

        line = (
            f"{timestamp()} | [{query_type.upper()}] | SUCCESS: {success} | QUERY_NAME: {query_label} | "
            f"EXEC_TIME: {round(execution_time, 4)}s | ROWS: {rowcount} | "
            f"CPU: {round(cpu_pct, 2)}% | MEM: {round(mem_rss_mb, 2)}MB | QUERY: {query.strip()}"
        )

        if setup_queries:
            setup_counts = defaultdict(int)
            for q in setup_queries:
                setup_counts[get_query_type(q)] += 1
            setup_summary = ', '.join(f"{k}: {v}" for k, v in setup_counts.items())
            line += f" | SETUP: {len(setup_queries)} query(ies), types: {setup_summary}"

        if not success and error_message:
            line += f"  <-- ERROR: {error_message}"

        return line

    def log_regular_test(self, *args, **kwargs):
        self.record_regular_metrics(
            kwargs["execution_time"], kwargs["query_type"], kwargs["success"]
        )
        log_line = self.format_regular_log_line(*args, **kwargs)
        self._write_log_line(log_line)

    def log_skip(self, query_label, reason=None):
        self.skipped_test_count += 1
        line = f"{timestamp()} | _SKIPPED_ | NAME: {query_label}"
        if isinstance(reason, str):
            line += f" | REASON: {reason}"
        elif reason is True:
            line += " | REASON: --"
        elif reason is not None:
            line += f" | REASON: invalid skip reason type ({type(reason).__name__})"
        self._write_log_line(line)

    def finish(self):
        import statistics

        duration = time.time() - self.start_time

        median_by_type = {
            qtype: statistics.median(times)
            for qtype, times in self.by_type.items()
        }

        sys_info = get_system_info()

        summary = (
            f"Test File Name: {self.test_file_name}\n"
            f"Selected Suites: {', '.join(self.selected_suites)}\n"
            f"Run Test Time ID: {self.log_file_id}\n"
            f"--- Test Summary ---\n\n"
            "--- System Info ---\n"
            f"CPU: {sys_info['CPU']}\n"
            f"CPU Cores: {sys_info['CPU_CORES']}\n"
            f"Total System Memory: {sys_info['TOTAL_MEMORY_GB']} GB\n"
            "\n--- Total Summary ---\n"
            f"Timestamp: {timestamp()}\n"
            f"Suites Run: {', '.join(self.suites_run)}\n"
            f"Tests Skipped: {self.skipped_test_count}\n"
            f"Total Tests Run: {self.run_tests_count}\n"
            f"Total Test Suite Time: {duration:.6f} sec\n"
            f"Total Query Time (cumulative regular+parallel): {self.total_exec_time:.6f} sec\n"
            f"\n--- REGULAR QUERY STATS ---\n"
            f"Total Tests: {len(self.regualar_execution_times)}\n"
            f"Total Time: {sum(self.regualar_execution_times):.4f} sec\n"
            f"Avg Query Exec Time: {self.total_exec_time / self.run_tests_count if self.run_tests_count else 0:.6f} sec\n"
            f"Min Query Exec Time: {min(self.regualar_execution_times) if self.regualar_execution_times else 0:.6f} sec\n"
            f"Max Query Exec Time: {max(self.regualar_execution_times) if self.regualar_execution_times else 0:.6f} sec\n"
            f"\n--- PARALLEL QUERY STATS ---\n"
            f"Total Tests: {len(self.parallel_execution_stats)}\n"
            f"Total Time: {sum(p[0] for p in self.parallel_execution_stats):.4f} sec\n"
            f"Avg Execution Time: {sum((p[3] for p in self.parallel_execution_stats)) / len(self.parallel_execution_stats) if self.parallel_execution_stats else 0:.4f} sec\n"
            f"Min Execution Time: {max((p[1] for p in self.parallel_execution_stats), default=0):.4f} sec\n"
            f"Max Execution Time: {min((p[2] for p in self.parallel_execution_stats), default=0):.4f} sec\n"
            f".............................................\n"
            f"Failed Queries: {self.fail_count}\n"
            f"Median Time by Query Type: { {k: round(v, 6) for k, v in median_by_type.items()} }\n"
            f"Average CPU Usage: {sum(self.cpu_usages) / len(self.cpu_usages):.6f}%\n"
            f"Peak Memory Usage: {max(self.memory_usages):.6f} MB\n"
        )

        with open(self.log_file.replace(".txt", ".summary.txt"), "w", encoding="utf-8") as f:
            f.write(summary)

        print(summary)
        return self.log_file
