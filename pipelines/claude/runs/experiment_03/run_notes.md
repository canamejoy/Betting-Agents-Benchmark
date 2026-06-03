# Experiment 03 — Live Iteration Speed: Run Notes

**Tool:** Claude Code  
**Date:** 2026-06-03  
**Source:** `broken_pipeline/pipeline.py` → fixed in `pipeline_03.py`  
**Run command:** `python pipelines/claude/run_experiment_03.py`

## Bugs Found and Fixed

### Bug 1 — Implied probability formula (line 46)

```python
# BROKEN
def compute_implied_probability(odds_decimal):
    return odds_decimal / (1 + odds_decimal)   # wrong: gives ~0.60 for odds 1.5

# FIXED
def compute_implied_probability(odds_decimal):
    return 1.0 / odds_decimal                  # correct: gives ~0.667 for odds 1.5
```

**Impact:** Wrong implied probs inflated EV estimates and distorted edge calculation.
The broken formula converges to 1.0 as odds grow, rather than 0. For odds=2.0,
buggy=0.667 vs correct=0.500 — a 33% overestimate of the bookmaker's implied probability.

### Bug 2 — Push treated as loss (lines 88–91)

```python
# BROKEN
if result == "win":
    pnl = stake * (row["odds_decimal"] - 1)
else:                  # catches both "loss" AND "push"
    pnl = -stake

# FIXED
if result == "win":
    pnl = stake * (row["odds_decimal"] - 1)
elif result == "loss":
    pnl = -stake
else:                  # push: stake returned, net = 0
    pnl = 0.0
```

**Impact:** Every push incorrectly deducted one full stake unit from the bankroll.

### Bug 3 — ROI divided by bet count (line 116)

```python
# BROKEN
roi = total_profit / len(results_df)   # divides by number of bets

# FIXED
roi = total_profit / total_stake if total_stake > 0 else 0.0
```

**Impact:** ROI figure was dimensionally wrong (profit/count has no financial meaning).
On flat staking (1 unit) the numbers happened to coincide, but any non-unit stake
size would produce a completely wrong ROI.

### Secondary Fix — Encoder fit on full dataset

The broken pipeline called `build_features(df)` on the full dataset before splitting,
fitting LabelEncoder on both train and test rows. Fixed by splitting first, then fitting
encoders only on `train_df`.

## Results (Fixed Pipeline)

| Metric | Value |
|--------|-------|
| Total profit | 6.05 units |
| ROI | 43.21% |
| Hit rate | 69.23% |
| Bet count | 14 |
| Max drawdown | 0.0012 (relative, as in original structure) |
| Runtime | 0.03 s |

Matches Experiment 01 exactly (same model, same data, flat staking).

## Regression Tests

15 regression tests added in `tests/test_pipeline_03_regressions.py`:
- `TestImpliedProbabilityBug` (7 tests): verifies correct 1/odds formula
- `TestPushSettlementBug` (4 tests): verifies push returns 0 pnl
- `TestROIBug` (4 tests): verifies ROI = profit / total_staked

## Debug Timeline

- Identified all 3 bugs on first read of broken_pipeline/pipeline.py
- Fixed in single pass, no iteration needed
- All 46 tests passed on second pytest run (4 test-setup issues fixed on first run)
