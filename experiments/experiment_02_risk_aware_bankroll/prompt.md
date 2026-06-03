# Experiment 02 Prompt - Risk-Aware Bankroll

Copy this prompt verbatim when starting the experiment with each tool.

---

You are extending a betting-agent pipeline for the Betting Agents Benchmark.

Read these files before writing any code:
- Shared rules: `instructions/shared_instructions.md`
- Experiment spec: `experiments/experiment_02_risk_aware_bankroll/README.md`
- Dataset: `data/sample_betting_data.csv`

Implement your solution inside `pipelines/<your-tool>/src/`. If you completed Experiment 01, extend that code. Otherwise build from scratch following the Experiment 01 baseline spec first, then add the features below.

## Task

Extend the baseline betting pipeline with bankroll management and explicit risk controls.

Add the following to the baseline:

1. Start with a configurable initial bankroll, default `1000` units.
2. Replace flat staking with fractional Kelly staking: `stake = (edge / (odds - 1)) * kelly_fraction * bankroll`, where `edge = model_probability - implied_probability` and `kelly_fraction` defaults to `0.25`.
3. Cap each stake at `max_stake_pct * bankroll`, default `5%` of current bankroll.
4. Cap total stakes per event date at `max_daily_exposure_pct * bankroll`, default `10%`.
5. Track bankroll after each bet settles. Wins add `stake * (odds - 1)`, losses subtract `stake`, and pushes return `stake`.
6. Compute and export risk metrics: `max_drawdown`, `profit_volatility`, `sharpe_like_ratio`, `max_stake`, `max_daily_exposure`, and `risk_of_ruin_proxy`.
7. Extend `metrics.json` with all risk metrics.

## Constraints

- Risk limits must be configurable: `kelly_fraction`, `max_stake_pct`, and `max_daily_exposure_pct`.
- Stake sizing must never use future outcomes.
- Bankroll must never go below zero. Enforce a floor of `0`.
- Include tests for Kelly formula, stake cap enforcement, daily exposure cap, and bankroll update after win/loss/push.

## Deliverables

- Extended source code in `pipelines/<your-tool>/src/`
- `metrics.json` with both betting and risk metrics
- `runs/YYYY-MM-DD_experiment_02/notes.md` with what changed from Experiment 01, commands used, and failures
