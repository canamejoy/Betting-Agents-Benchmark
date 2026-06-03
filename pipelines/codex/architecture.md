# Codex Architecture Notes

Track the architecture Codex creates during each experiment.

## Suggested Modules

| Module | Responsibility |
| --- | --- |
| `data` | Load and validate input files |
| `features` | Build time-aware model features |
| `model` | Estimate probabilities |
| `betting` | Compute implied probability, EV, and bet selection |
| `risk` | Stake sizing and bankroll controls |
| `backtest` | Chronological simulation |
| `metrics` | Performance and risk metrics |
| `reporting` | Export JSON, CSV, plots, and logs |

## Notes

Record whether Codex follows this structure, improves it, or chooses another architecture.
