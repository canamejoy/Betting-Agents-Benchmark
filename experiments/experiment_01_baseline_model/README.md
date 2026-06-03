# Experiment 01: Baseline Model

## Purpose

Measure how quickly and reliably each tool can create a first reproducible betting pipeline.

## Task Prompt

Build a baseline betting-agent backtest using the shared dataset and shared instructions. The pipeline should load data, create simple features, estimate probabilities, select positive expected value bets, use flat staking, simulate results, and export metrics.

## Required Behavior

- Use chronological train/test split.
- Use simple, explainable features.
- Convert decimal odds to implied probabilities.
- Select bets with expected value above a configurable threshold.
- Use flat stake sizing.
- Export `metrics.json`.

## Suggested Acceptance Criteria

- Pipeline runs from one command.
- No future data leakage.
- Reports profit, ROI, hit rate, bet count, max drawdown, and runtime.
- Includes at least basic tests for odds conversion, EV, and ROI.

## Primary Metrics

- Time to first runnable pipeline.
- ROI.
- Total profit.
- Hit rate.
- Bet count.
- Max drawdown.
- Reproducibility score.
