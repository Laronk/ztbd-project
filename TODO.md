# 📋 Project TODO

## Test Execution Enhancements
- [ ] **Add test activation toggle**  
  Allow individual tests or test suites to be conditionally executed (e.g. via `"enabled": true/false` flag in JSON).

- [ ] **Support for setup queries per test case**  
  Enable pre-test setup actions (e.g. insert test data), and restore the base DB state after each test/suite.

- [ ] **Parallel Query Execution Feature**
  <!-- Core Logic -->
  - [x] Add support for `"run_parallel": true` flag in JSON queries
  - [x] Validate required fields:
    - [x] `simulated_client_number` (int, ≥ 2)
    - [x] `queries_per_time` (int, ≥ 1)
    - [x] `execution_loop_time_ms` (int, ≥ 100)
  - [x] Finall parallel query test definition has to follow the template:
  ```json
  {
    "Parallel Stress Tests": {
      "queries": [
        {
          "label": "Simulated lab session per client",
          "run_parallel": true,
          "setup": [
            "INSERT INTO patient (patientunitstayid, age, gender, hospitalid) VALUES (7777777, '30', 'Other', 5);"
          ],
          "query_seq": [
            "INSERT INTO lab (patientunitstayid, labname, labresult) VALUES (7777777, 'Na+', '137.0');",
            "INSERT INTO lab (patientunitstayid, labname, labresult) VALUES (7777777, 'K+', '4.5');",
            "DELETE FROM lab WHERE patientunitstayid = 7777777 AND labname IN ('Na+', 'K+');"
          ],
          "simulated_client_number": 3,
          "queries_per_time": 2,
          "execution_loop_time_ms": 1000
        }
      ]
    }
  }
  ```
  <!-- Thread Execution & Control -->
  - [ ] Spawn one thread per simulated client
  - [ ] Each thread:
    - [ ] Executes the query `queries_per_time` times
    - [ ] Sleeps appropriately to respect `execution_loop_time_ms`
    - [ ] Records execution time for each iteration
  - [ ] Aggregate per-thread performance metrics after execution
  <!-- Restrictions & Safety -->
  - [x] Create a `PARALLEL_EXECUTION_ALLOWED` set with disallowed query types:
    - `SELECT`, `INSERT`, `UPDATE`, `DELETE`
  - [x] Skip or warn if disallowed query types are found in a parallel block
  - [ ] Cap max threads to avoid overloading the DB (e.g. `MAX_PARALLEL_QUERIES`)
    - [ ] Write a general test system config file in python
  <!-- Setup Queries & Validation -->
  - [x] Allow `setup` field for parallel queries (must run once before threads)
  - [x] Validate `setup` query types against exclusion list
  - [x] Log setup phase execution and failure (if any)
  <!-- Logging Enhancements -->
  - [ ] Log per-thread execution time (min, max, avg)
  - [ ] Log total simulated clients
  - [ ] Log total number of query executions
  - [ ] Indicate if query was run in parallel in log line
  - [ ] Ensure logging is thread-safe (`threading.Lock` if needed)
  <!-- Testing & Debug -->
  - [x] Create a test suite category `"Parallel"` in `.json`
  - [x] Include sample queries with all new required flags
  - [ ] Verify behavior with both valid and invalid configs
  - [ ] Verify query results are consistent across threads (if applicable)

---

## Logging Improvements
- [ ] **Include time unit in summary statistics**  
  Example: `Median Time by Query Type: {'SELECT': 0.005442}` → `0.005442 s`

- [ ] **Print per-suite timing summary on execution**  
  Show **average**, **minimum**, and **maximum** execution times for each suite when tests are run.

- [ ] **Log per-suite timing stats to output files**  
  Extend summary logs to include avg/min/max query time per suite.

## Other
- [ ] **Perform test query result analysis**

- [ ] **Translate the queries from postgres to mongoDB format**