"""Tests for metrics calculations — especially ROI formula."""

import pytest
import pandas as pd
from pipelines.codex.src.metrics_calc import compute_betting_metrics


def _make_results(rows):
    return pd.DataFrame(rows, columns=["event_id", "result", "stake", "pnl", "bankroll"])


def test_roi_is_profit_over_staked_not_count():
    # 2 bets, stakes differ: one 10-unit win (+10), one 10-unit loss (-10)
    df = _make_results([
        ("E1", "win",  10.0,  10.0, 1010.0),
        ("E2", "loss", 10.0, -10.0, 1000.0),
    ])
    m = compute_betting_metrics(df, 0.5)
    assert m["total_staked"] == pytest.approx(20.0)
    assert m["total_profit"] == pytest.approx(0.0)
    assert m["roi"] == pytest.approx(0.0)


def test_roi_positive():
    df = _make_results([
        ("E1", "win", 10.0, 10.0, 1010.0),
    ])
    m = compute_betting_metrics(df, 0.1)
    # profit=10, staked=10, roi=1.0
    assert m["roi"] == pytest.approx(1.0)


def test_push_does_not_count_in_hit_rate():
    df = _make_results([
        ("E1", "win",  1.0,  1.0, 1001.0),
        ("E2", "push", 1.0,  0.0, 1001.0),
        ("E3", "loss", 1.0, -1.0, 1000.0),
    ])
    m = compute_betting_metrics(df, 0.1)
    # hit rate: 1 win / 2 settled = 0.5
    assert m["hit_rate"] == pytest.approx(0.5)


def test_bet_count():
    df = _make_results([
        ("E1", "win",  1.0, 1.0, 1001.0),
        ("E2", "loss", 1.0, -1.0, 1000.0),
    ])
    m = compute_betting_metrics(df, 0.1)
    assert m["bet_count"] == 2


def test_empty_results():
    df = pd.DataFrame(columns=["event_id", "result", "stake", "pnl", "bankroll"])
    m = compute_betting_metrics(df, 0.0)
    assert m["bet_count"] == 0
    assert m["roi"] == 0.0
