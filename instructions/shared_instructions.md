# Shared Instructions

These instructions must be given to both Codex and Claude Code before each experiment.

## Role

You are building a reproducible betting-agent pipeline for historical backtesting. Your output must be testable, documented, and honest about uncertainty.

## Core Requirements

- Use the same dataset and schema for every run.
- Avoid future data leakage.
- Separate training data from evaluation data chronologically.
- Compute probabilities, expected value, selected bets, stake sizes, and backtest results.
- Export metrics in a machine-readable format.
- Explain assumptions and limitations.

## Betting Rules

- Use decimal odds.
- Implied probability is `1 / odds_decimal`.
- Expected value per unit stake is `(model_probability * odds_decimal) - 1`.
- A bet is eligible when expected value is positive and above the configured threshold.
- Pushes should return stake and should not count as wins or losses.

## Risk Rules

- Track bankroll over time.
- Report max drawdown.
- Cap stake size.
- Cap total exposure per event or day when implemented.
- Do not allow negative stakes.

## Engineering Rules

- Prefer small, readable modules.
- Include a simple run command.
- Include tests for metric calculations and staking logic.
- Keep configuration explicit.
- Log runtime and generated outputs.

## Required Outputs

Each experiment run should produce:

- Source code or notebook for the pipeline.
- A metrics file, preferably `metrics.json`.
- A short run note describing what happened.
- Any plots, tables, or logs that help evaluate the run.

## Prohibited Shortcuts

- Do not use final game results as model features.
- Do not tune thresholds on the evaluation period and then report the same period as unbiased.
- Do not silently drop losing bets.
- Do not report ROI without stake totals and bet count.
- Do not claim profitability without a backtest.
