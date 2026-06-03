# Experiment 02 — Risk-Aware Bankroll: Run Notes

**Tool:** Claude Code  
**Date:** 2026-06-03  
**Run command:** `python pipelines/claude/run_experiment_02.py`

## Results

Starting bankroll: 1,000 units

| Metric | Value |
|--------|-------|
| Total profit | 274.72 units |
| Final bankroll | 1,274.72 units (+27.5%) |
| ROI | 49.81% of total staked |
| Hit rate | 69.23% (same model as Exp 01) |
| Bet count | 14 (same bets selected) |
| Max drawdown | 46.47 units (4.65% of bankroll) |
| Profit volatility | 39.12 units/bet |
| Sharpe-like ratio | 0.5015 |
| Max single stake | 59.90 units (5.99% of bankroll at time) |
| Max daily exposure | 59.90 units |
| Risk of ruin proxy | 0.046 |

## Kelly Staking Parameters

| Parameter | Value |
|-----------|-------|
| kelly_fraction | 0.25 |
| max_stake_pct | 0.05 (5% of current bankroll) |
| max_daily_exposure_pct | 0.10 (10% of current bankroll) |

## Formula Used

```
edge = model_prob - (1 / odds_decimal)
stake = (edge / (odds_decimal - 1)) * kelly_fraction * bankroll
stake = min(stake, bankroll * max_stake_pct)
stake = min(stake, max(0, bankroll * daily_cap - day_used))
```

## Decisions

- Kelly is calculated dynamically (bankroll updates after each bet)
- Daily exposure cap recomputed per bet based on current bankroll
- Positive CLV (+0.148 avg) explains why Kelly sizing amplifies profit vs flat staking
- All 14 bets placed on separate days → daily cap never triggered on this dataset
