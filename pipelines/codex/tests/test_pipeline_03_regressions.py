"""Regression tests covering each bug found in the broken pipeline."""

import pytest
from pipelines.codex.src.pipeline_03 import compute_implied_probability, compute_metrics
import pandas as pd


# --- Bug 1: implied probability formula ---

def test_implied_probability_correct_formula():
    # 2.0 decimal odds → 50% probability
    assert compute_implied_probability(2.0) == pytest.approx(0.5)


def test_implied_probability_rejects_broken_formula():
    # Broken formula: 2/(1+2) = 0.667, not 0.5
    assert compute_implied_probability(2.0) != pytest.approx(2.0 / 3.0)


def test_implied_probability_4_decimal():
    assert compute_implied_probability(4.0) == pytest.approx(0.25)


# --- Bug 2: ROI formula ---

def _make_results_df(rows):
    return pd.DataFrame(rows, columns=["event_id", "result", "stake", "pnl", "bankroll"])


def test_roi_divides_by_total_staked():
    results_df = _make_results_df([
        ("E1", "win",  5.0,  5.0, 1005.0),
        ("E2", "loss", 5.0, -5.0, 1000.0),
    ])
    m = compute_metrics(results_df, results_df, 0.0, 0.1)
    # total_staked=10, total_profit=0 → roi=0.0
    assert m["roi"] == pytest.approx(0.0)
    # Broken formula would give 0 / 2 = 0.0 in this case too;
    # test with non-zero profit:
    results_df2 = _make_results_df([
        ("E1", "win", 10.0, 20.0, 1020.0),
    ])
    m2 = compute_metrics(results_df2, results_df2, 0.0, 0.1)
    # profit=20, staked=10 → roi=2.0
    # broken formula: 20/1 = 20.0
    assert m2["roi"] == pytest.approx(2.0)


# --- Bug 3: push pnl ---

def test_push_returns_zero_pnl():
    from pipelines.codex.src.pipeline_03 import simulate_backtest
    import pandas as pd

    bets = pd.DataFrame([{
        "event_id": "E1",
        "result": "push",
        "odds_decimal": 2.0,
    }])
    results_df, _ = simulate_backtest(bets, stake=10.0)
    assert results_df.iloc[0]["pnl"] == pytest.approx(0.0)


def test_push_does_not_reduce_bankroll():
    from pipelines.codex.src.pipeline_03 import simulate_backtest
    bets = pd.DataFrame([{
        "event_id": "E1",
        "result": "push",
        "odds_decimal": 2.0,
    }])
    results_df, _ = simulate_backtest(bets, stake=10.0)
    # bankroll should remain at initial (1000)
    assert results_df.iloc[0]["bankroll"] == pytest.approx(1000.0)
