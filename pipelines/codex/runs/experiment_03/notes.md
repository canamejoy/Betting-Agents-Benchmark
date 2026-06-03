# Experiment 03 — Debug Run Notes

**Date:** 2026-06-03  
**Tool:** Claude Code (codex-run branch)  
**Starting file:** `experiments/experiment_03_live_iteration_speed/broken_pipeline/pipeline.py`

## Bugs Found

### Bug 1: `compute_implied_probability` — wrong formula
- **Location:** `pipeline.py` line 46
- **Root cause:** Used `odds / (1 + odds)` (logistic-style transform) instead of `1 / odds` (correct decimal-odds formula).
- **Impact:** Inflated implied probabilities → underestimated edge → wrong EV scores and bet selection.
- **Fix:** Changed to `return 1.0 / odds_decimal`.
- **Time to find:** ~30 seconds (spotted in first code review pass).

### Bug 2: ROI divides by bet count instead of total staked
- **Location:** `pipeline.py` line 116
- **Root cause:** `roi = total_profit / len(results_df)` divides by number of bets, not by total staked. ROI is defined as profit per unit staked.
- **Impact:** ROI number is misleading and not comparable across runs with different stake sizes.
- **Fix:** Changed to `roi = total_profit / total_stake if total_stake > 0 else 0.0`.
- **Time to find:** ~1 minute (spotted during metrics review).

### Bug 3: Push treated as loss
- **Location:** `pipeline.py` lines 88–91
- **Root cause:** `else: pnl = -stake` lumped push with loss. Pushes should return the stake (pnl = 0).
- **Impact:** Bankroll incorrectly decreased on push results; drawdown inflated.
- **Fix:** Added explicit `elif result == "push": pnl = 0.0` branch.
- **Time to find:** ~2 minutes (noticed bankroll declined on a push row in results).

## Results (Fixed)

| Metric | Value |
|---|---|
| total_profit | 6.05 |
| roi | 0.4321 |
| total_staked | 14.0 |
| hit_rate | 0.6923 |
| bet_count | 14 |
| max_drawdown | 0.0012 |
| runtime_seconds | 0.02 |

## Regression Tests Added

- `test_implied_probability_correct_formula` — verifies 1/odds formula
- `test_implied_probability_rejects_broken_formula` — confirms old formula rejected
- `test_roi_divides_by_total_staked` — ensures ROI uses staked denominator
- `test_push_returns_zero_pnl` — push bet has zero pnl
- `test_push_does_not_reduce_bankroll` — bankroll unchanged after push

## Commands Used

```powershell
python pipelines/codex/run_experiment_03.py
python -m pytest pipelines/codex/tests/test_pipeline_03_regressions.py -v
```

## Total Time

~5 minutes from receiving broken_pipeline/pipeline.py to all tests passing.
