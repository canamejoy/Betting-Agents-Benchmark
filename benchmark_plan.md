# Benchmark Plan

## Objective

Measure how Codex and Claude Code perform when building betting-agent systems from the same problem statement, data assumptions, experiments, and scoring rules.

The benchmark compares two dimensions:

- Betting-agent output quality: how profitable, calibrated, and risk-aware the produced pipeline is.
- Engineering process quality: how fast, reliable, reproducible, and maintainable each tool's implementation is.

## Shared Problem

Build a sports betting agent that receives historical game data and betting odds, predicts useful probabilities, identifies positive expected value bets, sizes stakes, and reports results.

Minimum input schema:

| Field | Description |
| --- | --- |
| `event_id` | Unique game or market identifier |
| `event_date` | Date of the event |
| `sport` | Sport or league |
| `home_team` | Home team name |
| `away_team` | Away team name |
| `market` | Bet market, such as moneyline or spread |
| `selection` | Bet selection |
| `odds_decimal` | Decimal odds available before the event |
| `closing_odds_decimal` | Optional closing decimal odds |
| `result` | Binary win/loss/push outcome for the selection |
| `stake` | Stake amount, if already available |

## General Pipeline

1. Data ingestion
   - Load CSV or parquet data.
   - Validate required columns.
   - Sort by event date to avoid leakage.

2. Data cleaning
   - Remove invalid odds.
   - Handle missing results.
   - Normalize team and market names.
   - Mark pushes separately from wins and losses.

3. Feature engineering
   - Historical team strength.
   - Recent form.
   - Market-implied probability.
   - Odds movement, when closing odds exist.
   - League, market, and home/away indicators.

4. Probability modeling
   - Estimate probability for each selection.
   - Keep training windows time-aware.
   - Report calibration diagnostics.

5. Bet selection
   - Convert odds to implied probability.
   - Compute edge and expected value.
   - Select bets above a configurable edge threshold.

6. Stake sizing
   - Start with flat staking in experiment 1.
   - Add fractional Kelly or capped proportional staking in experiment 2.
   - Enforce max stake and max daily exposure.

7. Backtesting
   - Simulate bets chronologically.
   - Track bankroll, drawdown, exposure, and bet count.
   - Prevent future data leakage.

8. Reporting
   - Export metrics as JSON or CSV.
   - Include plots or tables when practical.
   - Log assumptions, failures, and runtime.

## Architecture Comparison

Evaluate whether each assistant naturally creates:

- Clear module boundaries for data, features, model, betting, risk, and reporting.
- Reproducible configuration.
- Useful tests for leakage, odds conversion, staking, and metric calculations.
- Simple command-line or script entry points.
- Logs or artifacts that make experiments repeatable.

## Benchmark Controls

Use the same:

- Dataset.
- Experiment prompt.
- Runtime environment.
- Time budget.
- Number of allowed iterations.
- Acceptance criteria.
- Scoring sheet.

Document any deviation immediately.

## Recommended Benchmark Round

For each experiment:

1. Start a timer.
2. Run Codex with the experiment prompt.
3. Run Claude Code with the same prompt.
4. Execute the generated pipeline if possible.
5. Fill the scorecard.
6. Save tool outputs and notes in each pipeline folder.

## Final Comparison Report

The final report should include:

- Tool name.
- Experiment name.
- Runtime.
- Successful commands.
- Failed commands.
- Main artifacts created.
- Betting metrics.
- Risk metrics.
- Engineering quality score.
- Notes on prompt adherence and architecture.
