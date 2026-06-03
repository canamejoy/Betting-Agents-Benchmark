import pytest

from src.risk import kelly_stake, cap_stake


def test_kelly_stake_positive_edge():
    # model_prob=0.55, odds=2.0 → implied=0.5, edge=0.05, b=1.0
    # stake = (0.05/1.0) * 0.25 * 1000 = 12.5
    stake = kelly_stake(0.55, 2.0, 0.25, 1000.0)
    assert abs(stake - 12.5) < 1e-6


def test_kelly_stake_zero_edge():
    stake = kelly_stake(0.50, 2.0, 0.25, 1000.0)
    assert stake == 0.0


def test_kelly_stake_negative_edge():
    stake = kelly_stake(0.40, 2.0, 0.25, 1000.0)
    assert stake == 0.0


def test_kelly_stake_odds_one():
    stake = kelly_stake(0.80, 1.0, 0.25, 1000.0)
    assert stake == 0.0


def test_cap_stake_below_limit():
    assert cap_stake(10.0, 1000.0, 0.05) == 10.0


def test_cap_stake_above_limit():
    assert cap_stake(100.0, 1000.0, 0.05) == 50.0


def test_cap_stake_exactly_at_limit():
    assert cap_stake(50.0, 1000.0, 0.05) == 50.0
