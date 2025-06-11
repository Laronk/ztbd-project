from collections import defaultdict
import os
import time
import psutil
from .log_utils import get_query_type, get_system_info, timestamp, get_log_filename


class QueryLogger:
    def __init__(self, log_file=None):
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
            f.write(f"--- Query Benchmark Log ({timestamp()}) ---\n\n")

    def log_parallel_test(self, query_label, query_type, query, execution_time, min_time, max_time, avg_time, rowcount, success=True, setup_queries=[], error_message=None):
        self.run_tests_count += 1
        self.total_exec_time += execution_time
        # Calculate execution time stats for parallel tests separately 
        self.parallel_execution_stats.append((execution_time, min_time, max_time, avg_time))
       
        if not success:
            self.fail_count += 1

        # TODO: check correct processing of CPU and memory usage 
        cpu_pct = self.process.cpu_percent(interval=0.1)
        mem_rss_mb = self.process.memory_info().rss / (1024 * 1024)

        self.cpu_usages.append(cpu_pct)
        self.memory_usages.append(mem_rss_mb)

        # Ordered log format:
        log_line = (
            f"{timestamp()} | _{query_type.upper()}_ | SUCCESS: {success} | QUERY_NAME: {query_label} | "
            f"EXEC_TOTAL_TIME: {round(execution_time, 4)}s | EXEC_MIN_TIME: {round(min_time, 4)}s | EXEC_MAX_TIME: {round(max_time, 4)}s | EXEC_AVG_TIME: {round(avg_time, 4)}s | ROWS: {rowcount} | "
            f"CPU: {round(cpu_pct, 2)}% | MEM: {round(mem_rss_mb, 2)}MB | QUERY: {query.strip()}"
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

    def log_regular_test(self, query_label, query_type, query, execution_time, rowcount, success=True, setup_queries=[], error_message=None):
        self.run_tests_count += 1
        self.total_exec_time += execution_time
        self.regualar_execution_times.append(execution_time)
        if not success:
            self.fail_count += 1

        self.by_type[query_type].append(execution_time)

        # TODO: check correct processing of CPU and memory usage 
        cpu_pct = self.process.cpu_percent(interval=0.1)
        mem_rss_mb = self.process.memory_info().rss / (1024 * 1024)

        self.cpu_usages.append(cpu_pct)
        self.memory_usages.append(mem_rss_mb)

        # Ordered log format:
        log_line = (
            f"{timestamp()} | [{query_type.upper()}] | SUCCESS: {success} | QUERY_NAME: {query_label} | "
            f"EXEC_TIME: {round(execution_time, 4)}s | ROWS: {rowcount} | "
            f"CPU: {round(cpu_pct, 2)}% | MEM: {round(mem_rss_mb, 2)}MB | QUERY: {query.strip()}"
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
    
    def log_skip(self, query_label, reason=None):
        self.skipped_test_count += 1
        log_line = (
            f"{timestamp()} | _SKIPPED_ | NAME: {query_label}"
        )
        
        if isinstance(reason, str):
            log_line += f" | REASON: {reason}"
        elif reason is True:
            log_line += f" | REASON: --"
        elif reason is not None:
            log_line += f" | REASON: invalid skip reason type ({type(reason).__name__})"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")

    def finish(self):
        import statistics
        import time

        duration = time.time() - self.start_time
        
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
            f"Tests Skipped: {self.skipped_test_count}\n"
            f"Total Tests Run: {self.run_tests_count}\n"
            f"Total Test Suite Time: {duration:.6f} sec\n"
            f"Total Query Time (cumulative regular+parallel): {self.total_exec_time:.6f} sec\n"
            f"--- REGULAR QUERY STATS ---\n"
            f"Total Tests: {len(self.regualar_execution_times)}\n"
            f"Total Time: {sum(exec_time for exec_time in self.regualar_execution_times):.4f} sec\n"
            f"Average Query Time: {self.total_exec_time / self.run_tests_count if self.run_tests_count else 0:.6f} sec\n"
            f"Fastest Query Time: {max(self.regualar_execution_times) if self.regualar_execution_times else 0:.6f} sec\n"
            f"Slowest Query Time: {min(self.regualar_execution_times) if self.regualar_execution_times else 0:.6f} sec\n"
            f"\n--- PARALLEL QUERY STATS ---\n"
            f"Total Tests: {len(self.parallel_execution_stats)}\n"
            f"Total Time: {sum(p[0] for p in self.parallel_execution_stats):.4f} sec\n"
            f"Min Execution Time: {min((p[1] for p in self.parallel_execution_stats), default=0):.4f} sec\n"
            f"Max Execution Time: {max((p[2] for p in self.parallel_execution_stats), default=0):.4f} sec\n"
            f"Avg Execution Time: {sum((p[3] for p in self.parallel_execution_stats)) / len(self.parallel_execution_stats) if self.parallel_execution_stats else 0:.4f} sec\n"
            f".............................................\n"
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