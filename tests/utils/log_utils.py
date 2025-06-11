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


def get_file_name_from_path(path):
    # returns file name with extension from a given file path
    # gives rest of path after last slash
    return os.path.basename(path)
    