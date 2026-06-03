# Betting Agents Benchmark

Benchmark project for comparing betting-agent development using Codex and Claude Code across pipelines, architectures, metrics, betting performance, risk, and speed.

This repository is organized so both tools solve the same betting-agent problem under the same data, prompts, experiments, and scoring rules.

## Goal

Compare how Codex and Claude Code perform when asked to build and improve betting pipelines for sports betting decisions.

The comparison focuses on:

- Betting quality: profit, ROI, hit rate, calibration, and closing-line value.
- Risk control: bankroll drawdown, exposure, variance, and limit discipline.
- Engineering speed: time to first runnable pipeline, iteration speed, and defects.
- Architecture quality: reproducibility, modularity, observability, and testability.

## Repository Layout

```text
.
|-- benchmark_plan.md
|-- instructions/
|   `-- shared_instructions.md
|-- metrics/
|   |-- metrics.md
|   `-- scorecard_template.csv
|-- experiments/
|   |-- experiment_01_baseline_model/
|   |-- experiment_02_risk_aware_bankroll/
|   `-- experiment_03_live_iteration_speed/
|-- pipelines/
|   |-- codex/
|   `-- claude/
`-- data/
    |-- README.md
    `-- sample_betting_data.csv
```

## General Pipeline

Each assistant should build the same end-to-end betting workflow:

1. Load historical games, odds, results, and optional market metadata.
2. Clean and validate the data.
3. Generate features for teams, games, market prices, and recent form.
4. Estimate win probabilities or expected value.
5. Select bets using a defined edge threshold.
6. Size stakes with a bankroll strategy.
7. Simulate bets on historical data.
8. Report performance, risk, speed, and implementation quality.

## Experiments

The initial benchmark has three experiments:

- `experiment_01_baseline_model`: simple reproducible prediction and bet-selection pipeline.
- `experiment_02_risk_aware_bankroll`: adds bankroll management and risk controls.
- `experiment_03_live_iteration_speed`: measures how quickly each assistant can debug, improve, and rerun the pipeline under a constrained task.

Each experiment folder includes a `prompt.md` file that can be copied verbatim into both tools.

## Tool-Specific Pipelines

- [Codex pipeline](pipelines/codex/README.md)
- [Claude Code pipeline](pipelines/claude/README.md)

Both pipelines should use the same shared instructions and metrics. Tool-specific differences should be documented, not hidden.

## Setup

Prerequisites: Python 3.10+

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

The synthetic dataset is already included at `data/sample_betting_data.csv`. No additional data download is needed to start.

## How To Run A Benchmark Round

1. Choose one experiment from `experiments/`.
2. Give Codex and Claude Code the same experiment prompt and shared instructions.
3. Record start time, end time, commands run, generated artifacts, and any failures.
4. Score each run using `metrics/scorecard_template.csv`.
5. Compare outputs in a short benchmark report.

## Important Note

This benchmark is for research and engineering comparison. It is not financial advice and should not be used to place real bets without independent validation.
