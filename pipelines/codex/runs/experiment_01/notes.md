# Experiment 01 — Baseline Run Notes

**Date:** 2026-06-03  
**Tool:** Claude Code (codex-run branch)  
**Command:** `python pipelines/codex/run_experiment_01.py`

## Assumptions

- Train/test split is strictly chronological (first 70% rows by date → train).
- Features fit only on training data; encoders applied to eval without refitting.
- Logistic regression, random_state=42 for reproducibility.
- Flat stake of 1.0 unit per selected bet.
- EV threshold: 0.05.

## Results

| Metric | Value |
|---|---|
| total_profit | 6.05 |
| roi | 0.4321 |
| total_staked | 14.0 |
| hit_rate | 0.6923 |
| bet_count | 14 |
| max_drawdown | 0.0012 |
| runtime_seconds | 0.04 |

## Commands Used

```powershell
.venv\Scripts\activate
python pipelines/codex/run_experiment_01.py
python -m pytest pipelines/codex/tests/ -v
```

## Failures

None. First run succeeded.

## Artifacts

- `metrics.json` — exported metrics
- `results.csv` — per-bet simulation results
