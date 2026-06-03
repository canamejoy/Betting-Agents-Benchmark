"""Tests for odds conversion, EV, and bet selection."""

import pytest
import pandas as pd
from pipelines.codex.src.features import implied_probability
from pipelines.codex.src.betting import compute_ev, select_bets


def test_implied_probability_basic():
    assert implied_probability(2.0) == pytest.approx(0.5)
    assert implied_probability(4.0) == pytest.approx(0.25)
    assert implied_probability(1.5) == pytest.approx(1 / 1.5)


def test_implied_probability_not_old_formula():
    # The broken pipeline used odds/(1+odds) which equals e.g. 2/3 not 1/2
    result = implied_probability(2.0)
    assert result != pytest.approx(2.0 / 3.0), "Used wrong formula odds/(1+odds)"


def test_compute_ev_positive():
    # 60% model prob on 2.0 odds → EV = 0.60*2.0 - 1 = 0.20
    assert compute_ev(0.60, 2.0) == pytest.approx(0.20)


def test_compute_ev_negative():
    # 40% model prob on 2.0 odds → EV = 0.40*2.0 - 1 = -0.20
    assert compute_ev(0.40, 2.0) == pytest.approx(-0.20)


def test_compute_ev_zero():
    # EV = 0 when model prob equals implied prob
    assert compute_ev(0.50, 2.0) == pytest.approx(0.0)


def test_select_bets_filters_threshold():
    df = pd.DataFrame({
        "event_id": ["A", "B", "C"],
        "odds_decimal": [2.0, 3.0, 1.8],
        "result": ["win", "loss", "push"],
        "event_date": ["2024-01-01"] * 3,
    })
    probs = [0.60, 0.20, 0.55]  # EVs: 0.20, -0.40, -0.01
    bets = select_bets(df, probs, ev_threshold=0.05)
    assert len(bets) == 1
    assert bets.iloc[0]["event_id"] == "A"


def test_select_bets_empty_when_none_qualify():
    df = pd.DataFrame({
        "event_id": ["A"],
        "odds_decimal": [2.0],
        "result": ["loss"],
        "event_date": ["2024-01-01"],
    })
    bets = select_bets(df, [0.40], ev_threshold=0.05)
    assert len(bets) == 0
