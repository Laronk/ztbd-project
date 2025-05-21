# client number has to be specified
# client number has to be an integer
# client number has to be greater-equal than 2
def validate_simulated_client_number(value):
    if value is None:
        return False, "'simulated_client_number' is required"
    if not isinstance(value, int):
        return False, "'simulated_client_number' must be an integer"
    if value < 2:
        return False, "'simulated_client_number' must be ≥ 2"
    return True, None

# queries per time has to be specified
# queries per time has to be an integer
# queries per time has to be greater-equal to 1
def validate_queries_per_time(value):
    if value is None:
        return False, "'queries_per_time' is required"
    if not isinstance(value, int):
        return False, "'queries_per_time' must be an integer"
    if value < 1:
        return False, "'queries_per_time' must be ≥ 1"
    return True, None

# execution loop time has to be specified
# execution loop time has to be an integer
# execution loop time has to be greater-equal to 100 (ms)
def validate_execution_loop_time_ms(value):
    if value is None:
        return False, "'execution_loop_time_ms' is required"
    if not isinstance(value, int):
        return False, "'execution_loop_time_ms' must be an integer"
    if value < 100:
        return False, "'execution_loop_time_ms' must be ≥ 100"
    return True, None

