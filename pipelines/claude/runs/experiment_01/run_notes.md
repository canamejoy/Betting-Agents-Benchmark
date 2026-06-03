# Experiment 01 — Baseline Model: Run Notes

**Tool:** Claude Code  
**Date:** 2026-06-03  
**Run command:** `python pipelines/claude/run_experiment_01.py`

## Setup

- Python 3.14.5 managed by uv
- venv at `.venv/` — activate with `.venv\Scripts\activate`
- Install: `uv venv .venv && uv pip install pandas numpy scikit-learn matplotlib pytest`

## Process

Single-pass implementation: no debug iterations required.

1. Wrote 9 core modules (config, data, features, model, betting, risk, backtest, metrics_calc, reporting)
2. Wrote `pipeline_01.py` composing the modules
3. Wrote `run_experiment_01.py` entry point
4. First run produced clean output with correct metrics

## Results

| Metric | Value |
|--------|-------|
| Total profit | 6.05 units |
| ROI | 43.21% |
| Hit rate | 69.23% (9W 4L 1P / 13 non-push) |
| Bet count | 14 / 21 test rows (66.7% coverage) |
| Average EV | 0.352 |
| Closing-line value | +0.148 (model beats market close) |
| Max drawdown | 1.25 units |
| Runtime | 0.082 s |

## Decisions

- `FeatureEncoder` class fits on train data, transforms both splits — no leakage from label encoding
- Pushes: pnl = 0 (stake returned), counted in bet_count but excluded from hit_rate denominator
- ROI = total_profit / total_stake (14 units flat × 1 unit each)
- Logistic regression: `random_state=42, max_iter=1000`

## Caveats

Results on 21-row test set (synthetic data). Not predictive of real-world performance.
