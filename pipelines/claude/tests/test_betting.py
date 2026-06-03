import pandas as pd
import pytest

from src.betting import compute_ev, add_ev, select_bets


def test_compute_ev_positive():
    ev = compute_ev(0.60, 2.00)  # prob=0.6, odds=2.0 → EV = 0.6*2.0-1 = 0.20
    assert abs(ev - 0.20) < 1e-9


def test_compute_ev_negative():
    ev = compute_ev(0.40, 2.00)  # EV = -0.20
    assert abs(ev - (-0.20)) < 1e-9


def test_compute_ev_zero():
    ev = compute_ev(0.50, 2.00)  # breakeven
    assert abs(ev) < 1e-9


def test_add_ev_column():
    df = pd.DataFrame({
        "model_prob": [0.60, 0.40],
        "odds_decimal": [2.00, 2.00],
    })
    out = add_ev(df)
    assert "ev" in out.columns
    assert abs(out.iloc[0]["ev"] - 0.20) < 1e-9


def test_select_bets_filters_by_threshold():
    df = pd.DataFrame({
        "model_prob": [0.60, 0.45, 0.30],
        "odds_decimal": [2.0, 2.0, 2.0],
        "ev": [0.20, -0.10, -0.40],
    })
    bets = select_bets(df, ev_threshold=0.05)
    assert len(bets) == 1
    assert bets.iloc[0]["ev"] == 0.20


def test_select_bets_empty_when_none_qualify():
    df = pd.DataFrame({
        "model_prob": [0.40],
        "odds_decimal": [2.0],
        "ev": [-0.20],
    })
    bets = select_bets(df, ev_threshold=0.05)
    assert len(bets) == 0
