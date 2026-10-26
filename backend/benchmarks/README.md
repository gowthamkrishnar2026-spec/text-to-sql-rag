# Benchmarks

This directory contains accuracy evaluation scripts for the AI Text-to-SQL system.
No changes are made to the running application — these scripts are pure read-only test infrastructure.

---

## Files

| File | Purpose |
|---|---|
| `benchmark_suite.json` | 30 hand-crafted NL→SQL ground-truth pairs (3 domains, 3 difficulty levels) |
| `run_benchmark.py` | Project-specific accuracy benchmark runner |
| `spider_eval.py` | Spider benchmark methodology + built-in Spider-adapted dataset |

---

## 1. Project Accuracy Benchmark

Runs 30 curated questions through the live API and scores 4 metrics:

| Metric | Description |
|---|---|
| **Generation Success** | Did the API return SQL without error? |
| **Execution Accuracy (EA)** | Does generated SQL return the same rows as gold SQL? *(Core Spider metric)* |
| **Column Match (CM)** | Do the returned column names match expected columns? |
| **Exact Match (EM)** | Does normalised generated SQL == normalised gold SQL? |

### Run

```bash
# From backend/ directory (server must be running on port 8000):
cd backend
PYTHONPATH=. python benchmarks/run_benchmark.py

# Filter by domain:
PYTHONPATH=. python benchmarks/run_benchmark.py --domain University
PYTHONPATH=. python benchmarks/run_benchmark.py --domain E-Commerce
PYTHONPATH=. python benchmarks/run_benchmark.py --domain Corporate

# Filter by difficulty:
PYTHONPATH=. python benchmarks/run_benchmark.py --difficulty easy
PYTHONPATH=. python benchmarks/run_benchmark.py --difficulty hard

# Save results to a JSON file:
PYTHONPATH=. python benchmarks/run_benchmark.py --output my_results.json

# Reduce delay between API calls (careful with rate limits):
PYTHONPATH=. python benchmarks/run_benchmark.py --delay 0.5
```

### Sample Output

```
  [01/30] UNI_001      Show all students                          EA✓   (312ms)
  [02/30] UNI_002      Show all students with CGPA greater than 8 EA✓   (285ms)
  ...

  ======================================================================
    AGGREGATE SCORES
  ======================================================================
    Total questions        : 30
    Generation Success     : 28/30  (93.3%)
    Execution Accuracy (EA): 24/30  (80.0%)
    Column Match       (CM): 25/30  (83.3%)
    Exact Match        (EM):  3/30  (10.0%)
    Avg latency            : 298 ms
```

> **Note:** Exact Match is intentionally low — Gemini generates semantically correct but syntactically different SQL.
> Execution Accuracy is the meaningful metric.

---

## 2. Spider Benchmark Evaluation

Implements the official [Spider](https://yale-nlp.github.io/spider/) evaluation metrics:
- **Execution Accuracy (EA)** — primary Spider leaderboard metric
- **Exact Set Match (EM)** — clause-level structural equivalence

### Run (built-in adapted dataset — no download needed)

```bash
cd backend
PYTHONPATH=. python benchmarks/spider_eval.py
```

### Run against the real Spider dev set (optional)

1. Download the Spider dataset from: https://yale-nlp.github.io/spider/
2. Extract the zip — you'll find `dev.json` inside.
3. Run:

```bash
PYTHONPATH=. python benchmarks/spider_eval.py --spider-dev /path/to/spider/dev.json
```

> The script auto-filters Spider questions to only those whose gold SQL
> references tables that exist in this project's database schema.

### Sample Output

```
  Spider Evaluation Results [Built-in Adapted Dataset]
  ======================================================================
    Total questions             : 30
    Execution Accuracy (EA) ★   : 22/30  (73.3%)
    Exact Set Match     (EM)    :  4/30  (13.3%)
    Avg Partial Clause Score    : 61.2%
    Avg latency                 : 301 ms
  ★ Execution Accuracy is the primary Spider leaderboard metric.
```

---

## Result Files

Each run saves a timestamped JSON to `backend/benchmarks/`:

```
benchmark_results_20260401_143022.json   ← from run_benchmark.py
spider_results_20260401_143510.json      ← from spider_eval.py
```

Both files share the same schema:
```json
{
  "run_timestamp": "2026-04-01T14:30:22",
  "metrics": { "execution_accuracy": 0.80, "avg_latency_ms": 298 },
  "cases": [
    {
      "id": "UNI_001",
      "prompt": "Show all students",
      "gold_sql": "SELECT ...",
      "generated_sql": "SELECT ...",
      "exec_accuracy": true,
      "latency_ms": 312
    }
  ]
}
```
