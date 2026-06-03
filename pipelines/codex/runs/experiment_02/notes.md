# Experiment 02 — Risk-Aware Bankroll Run Notes

**Date:** 2026-06-03  
**Tool:** Claude Code (codex-run branch)  
**Command:** `python pipelines/codex/run_experiment_02.py`

## Changes from Experiment 01

- Replaced flat staking with fractional Kelly: `stake = (edge/b) * kelly_fraction * bankroll`
- Kelly fraction: 0.25 (conservative)
- Max stake cap: 5% of current bankroll per bet
- Max daily exposure cap: 10% of current bankroll
- Added risk metrics: max_drawdown, profit_volatility, sharpe_like_ratio, max_stake, max_daily_exposure, risk_of_ruin_proxy

## Results

| Metric | Value |
|---|---|
| total_profit | 274.72 |
| roi | 0.4981 |
| total_staked | 551.53 |
| hit_rate | 0.6923 |
| bet_count | 14 |
| max_drawdown | 0.04 |
| profit_volatility | 39.12 |
| sharpe_like_ratio | 0.5015 |
| max_stake | 59.90 |
| max_daily_exposure | 59.90 |
| risk_of_ruin_proxy | 0.0 |

## Commands Used

```powershell
python pipelines/codex/run_experiment_02.py
```

## Failures

None.

## Notes

Kelly sizing scaled stakes significantly compared to flat (14 units total in Exp01 vs 551 units in Exp02). Max drawdown of 4% is within acceptable range. Risk of ruin proxy = 0 (bankroll never dropped below 20% of starting value).
