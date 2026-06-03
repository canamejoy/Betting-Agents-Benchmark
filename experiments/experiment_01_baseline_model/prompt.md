# Experiment 01 Prompt - Baseline Model

Copy this prompt verbatim when starting the experiment with each tool.

---

You are implementing a betting-agent pipeline for the Betting Agents Benchmark.

Read these files before writing any code:
- Shared rules: `instructions/shared_instructions.md`
- Experiment spec: `experiments/experiment_01_baseline_model/README.md`
- Dataset: `data/sample_betting_data.csv`

Implement your solution inside `pipelines/<your-tool>/src/`.

## Task

Build a baseline betting-agent backtest using the provided dataset and shared instructions.

The pipeline must:
1. Load `data/sample_betting_data.csv` and validate required columns.
2. Sort events chronologically and apply a train/test split using the first 70% of rows for training and the last 30% for evaluation.
3. Engineer simple features: market-implied probability, home/away indicator, sport encoding, and market type encoding.
4. Estimate win probability for each selection using a logistic regression or equivalent simple model trained only on training rows.
5. Compute expected value: `(model_probability * odds_decimal) - 1`.
6. Select bets where expected value exceeds a configurable threshold, default `0.05`.
7. Apply flat stake sizing, default `1` unit per selected bet.
8. Simulate the backtest chronologically on evaluation rows.
9. Export `metrics.json` with: `total_profit`, `roi`, `hit_rate`, `bet_count`, `max_drawdown`, and `runtime_seconds`.
10. Provide a single command to run the full pipeline and tests.

## Constraints

- No future data leakage. Training features must not use evaluation-period outcomes.
- Include tests for odds-to-implied-probability conversion, EV calculation, ROI formula, and flat staking.
- Keep configuration for threshold, stake size, and split ratio in a single config object or file.
- Record your run in `pipelines/<your-tool>/runs/YYYY-MM-DD_experiment_01/`.

## Deliverables

- Source code in `pipelines/<your-tool>/src/`
- `metrics.json`
- `runs/YYYY-MM-DD_experiment_01/notes.md` with assumptions, commands used, failures, and runtime
