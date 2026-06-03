# Evaluated Metrics

## Betting Performance Metrics

| Metric | Formula or Definition | Direction |
| --- | --- | --- |
| Total profit | Sum of bet returns minus stakes | Higher is better |
| ROI | Total profit divided by total staked | Higher is better |
| Hit rate | Winning bets divided by settled non-push bets | Higher is better, but not sufficient alone |
| Average EV | Mean expected value of selected bets | Higher is better |
| Closing-line value | Difference between taken price and closing price, converted to implied probability or odds movement | Higher is better |
| Bet count | Number of selected bets | Context metric |
| Coverage | Selected bets divided by available betting opportunities | Context metric |

## Risk Metrics

| Metric | Definition | Direction |
| --- | --- | --- |
| Max drawdown | Largest bankroll decline from peak to trough | Lower is better |
| Profit volatility | Standard deviation of daily or bet-level profit | Lower is better for same ROI |
| Sharpe-like ratio | Mean return divided by return standard deviation | Higher is better |
| Max stake | Largest single stake | Must respect constraints |
| Max daily exposure | Total stake risked on one day | Must respect constraints |
| Risk of ruin proxy | Share of runs or periods where bankroll falls below threshold | Lower is better |

## Speed Metrics

| Metric | Definition | Direction |
| --- | --- | --- |
| Time to first runnable pipeline | Minutes from prompt start to first successful execution | Lower is better |
| Total implementation time | Minutes from prompt start to accepted final output | Lower is better |
| Iterations to pass tests | Number of correction cycles needed | Lower is better |
| Runtime | Seconds needed to execute the benchmark pipeline | Lower is better |
| Debug recovery time | Time from first failure to fixed run | Lower is better |

## Architecture Metrics

Score each from 1 to 5.

| Metric | 1 | 3 | 5 |
| --- | --- | --- | --- |
| Reproducibility | Manual and unclear | Mostly runnable | Fully scripted and deterministic |
| Modularity | One tangled script | Some separation | Clean data/model/betting/risk/reporting modules |
| Leakage control | Not addressed | Partially handled | Explicit chronological splits and leakage tests |
| Observability | Little output | Basic logs | Clear metrics, logs, and artifacts |
| Test quality | No tests | Some metric tests | Focused tests for data, staking, EV, metrics, and leakage |
| Maintainability | Hard to modify | Acceptable | Simple, documented, configurable |

## Suggested Composite Score

Use this only as a summary, not as the whole evaluation.

```text
composite_score =
  0.35 * betting_score +
  0.25 * risk_score +
  0.20 * speed_score +
  0.20 * architecture_score
```

Normalize each category to a 0-100 scale before combining.
