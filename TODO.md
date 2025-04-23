### 📋 Project TODO

#### 🧪 Test Execution Enhancements
- [ ] **Add test activation toggle**  
  Allow individual tests or test suites to be conditionally executed (e.g. via `"enabled": true/false` flag in JSON).

- [ ] **Support for setup queries per test case**  
  Enable pre-test setup actions (e.g. insert test data), and restore the base DB state after each test/suite.

---

#### 📈 Logging Improvements
- [ ] **Include time unit in summary statistics**  
  Example: `Median Time by Query Type: {'SELECT': 0.005442}` → `0.005442 s`

- [ ] **Print per-suite timing summary on execution**  
  Show **average**, **minimum**, and **maximum** execution times for each suite when tests are run.

- [ ] **Log per-suite timing stats to output files**  
  Extend summary logs to include avg/min/max query time per suite.
