# Experiment 02: Risk-Aware Bankroll

## Purpose

Compare how each tool improves the baseline by adding bankroll management and explicit risk controls.

## Task Prompt

Extend the baseline betting-agent pipeline with bankroll tracking, capped stake sizing, fractional Kelly or proportional staking, daily exposure limits, and risk reporting. Preserve chronological evaluation and export all metrics.

## Required Behavior

- Start with a configurable bankroll.
- Size bets using fractional Kelly or capped proportional staking.
- Cap max stake per bet.
- Cap max daily exposure.
- Track bankroll after each bet.
- Report max drawdown and risk metrics.

## Suggested Acceptance Criteria

- Risk limits are configurable.
- Stake sizing has tests.
- Bankroll never uses future outcomes for sizing decisions.
- Metrics include ROI, profit, hit rate, max drawdown, max stake, max daily exposure, and risk of ruin proxy.

## Primary Metrics

- Risk-adjusted return.
- Max drawdown.
- Risk limit compliance.
- Profit volatility.
- Test quality.
- Maintainability.
