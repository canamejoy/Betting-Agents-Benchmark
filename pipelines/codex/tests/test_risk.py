"""Tests for Kelly staking, stake caps, and bankroll updates."""

import pytest
from pipelines.codex.src.risk import (
    kelly_stake,
    apply_daily_exposure_cap,
    update_bankroll,
    flat_stake,
)


def test_flat_stake_returns_amount():
    assert flat_stake(1.0) == pytest.approx(1.0)


def test_flat_stake_no_negative():
    assert flat_stake(-5.0) == 0.0


def test_kelly_stake_basic():
    # model_prob=0.55, odds=2.0, implied=0.50, edge=0.05, b=1.0
    # kelly = 0.05/1.0 = 0.05; fraction=0.25; bankroll=1000 → 12.50
    stake = kelly_stake(0.55, 2.0, 1000.0, 0.25, 0.10)
    assert stake == pytest.approx(12.50)


def test_kelly_stake_capped_by_max_pct():
    # Very high edge → kelly > max_stake_pct; cap should kick in
    stake = kelly_stake(0.90, 2.0, 1000.0, 1.0, 0.05)
    assert stake == pytest.approx(50.0)  # 5% of 1000


def test_kelly_stake_zero_when_no_edge():
    stake = kelly_stake(0.45, 2.0, 1000.0, 0.25, 0.10)
    assert stake == 0.0


def test_kelly_stake_zero_when_bankroll_zero():
    stake = kelly_stake(0.60, 2.0, 0.0, 0.25, 0.10)
    assert stake == 0.0


def test_daily_exposure_cap_reduces_stake():
    daily = {"2024-01-01": 80.0}
    # bankroll=1000, cap=10%=100, already 80 staked → max 20 more
    stake = apply_daily_exposure_cap(50.0, "2024-01-01", daily, 1000.0, 0.10)
    assert stake == pytest.approx(20.0)


def test_daily_exposure_cap_no_reduction_when_under():
    daily = {}
    stake = apply_daily_exposure_cap(5.0, "2024-01-01", daily, 1000.0, 0.10)
    assert stake == pytest.approx(5.0)


def test_daily_exposure_cap_zero_when_exhausted():
    daily = {"2024-01-01": 100.0}
    stake = apply_daily_exposure_cap(10.0, "2024-01-01", daily, 1000.0, 0.10)
    assert stake == 0.0


def test_update_bankroll_win():
    result = update_bankroll(1000.0, 10.0, "win", 2.0)
    assert result == pytest.approx(1010.0)  # +10*(2-1)


def test_update_bankroll_loss():
    result = update_bankroll(1000.0, 10.0, "loss", 2.0)
    assert result == pytest.approx(990.0)


def test_update_bankroll_push():
    result = update_bankroll(1000.0, 10.0, "push", 2.0)
    assert result == pytest.approx(1000.0)


def test_update_bankroll_never_negative():
    result = update_bankroll(5.0, 10.0, "loss", 2.0)
    assert result == 0.0
