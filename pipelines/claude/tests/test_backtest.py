import pandas as pd
import pytest

from src.backtest import simulate_flat, simulate_kelly


def _bets(records):
    return pd.DataFrame([{
        "event_id": i,
        "event_date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
        "odds_decimal": r["odds"],
        "result": r["result"],
        "model_prob": r.get("prob", 0.60),
        "ev": r.get("ev", 0.10),
    } for i, r in enumerate(records)])


def test_flat_win():
    bets = _bets([{"odds": 2.0, "result": "win"}])
    sim = simulate_flat(bets, flat_stake=1.0)
    assert abs(sim["total_profit"] - 1.0) < 1e-9
    assert abs(sim["total_stake"] - 1.0) < 1e-9


def test_flat_loss():
    bets = _bets([{"odds": 2.0, "result": "loss"}])
    sim = simulate_flat(bets, flat_stake=1.0)
    assert abs(sim["total_profit"] - (-1.0)) < 1e-9


def test_flat_push_returns_zero_pnl():
    bets = _bets([{"odds": 2.0, "result": "push"}])
    sim = simulate_flat(bets, flat_stake=1.0)
    assert sim["total_profit"] == 0.0
    assert sim["ledger"].iloc[0]["pnl"] == 0.0


def test_flat_drawdown():
    bets = _bets([
        {"odds": 2.0, "result": "win"},   # bankroll = +1
        {"odds": 2.0, "result": "loss"},  # bankroll = 0  → drawdown = 1
        {"odds": 2.0, "result": "loss"},  # bankroll = -1 → drawdown = 2
    ])
    sim = simulate_flat(bets, flat_stake=1.0)
    assert sim["max_drawdown"] == 2.0


def test_flat_empty_bets():
    sim = simulate_flat(pd.DataFrame(columns=["event_id","event_date","odds_decimal","result"]))
    assert sim["total_profit"] == 0.0
    assert sim["total_stake"] == 0.0


def test_kelly_stake_capped():
    # All on same day, large model_prob to generate big raw Kelly stake
    bets = _bets([{"odds": 2.0, "result": "win", "prob": 0.9}])
    sim = simulate_kelly(bets, initial_bankroll=1000.0, kelly_fraction=0.25,
                         max_stake_pct=0.05, max_daily_exposure_pct=0.10)
    assert len(sim["ledger"]) == 1
    assert sim["ledger"].iloc[0]["stake"] <= 1000.0 * 0.05 + 1e-9


def test_kelly_daily_exposure_cap():
    # With daily cap = stake cap = 5%, the first bet exhausts the day's budget.
    # Subsequent bets on the same day are skipped (bankroll drops after loss,
    # so remaining capacity goes negative).
    same_day = pd.Timestamp("2024-01-01")
    bets = pd.DataFrame([
        {"event_id": 0, "event_date": same_day, "odds_decimal": 2.0,
         "result": "loss", "model_prob": 0.80, "ev": 0.60},
        {"event_id": 1, "event_date": same_day, "odds_decimal": 2.0,
         "result": "loss", "model_prob": 0.80, "ev": 0.60},
        {"event_id": 2, "event_date": same_day, "odds_decimal": 2.0,
         "result": "loss", "model_prob": 0.80, "ev": 0.60},
    ])
    sim = simulate_kelly(bets, initial_bankroll=1000.0, kelly_fraction=0.25,
                         max_stake_pct=0.05, max_daily_exposure_pct=0.05)
    # First bet stakes 50 (5% of 1000), bankroll→950. daily cap now 950*0.05=47.5,
    # already used 50 → remaining ≤ 0 → bets 2 and 3 are skipped.
    assert len(sim["ledger"]) == 1
    assert sim["ledger"].iloc[0]["stake"] <= 1000.0 * 0.05 + 1e-6


def test_kelly_push_returns_stake():
    bets = _bets([{"odds": 2.0, "result": "push", "prob": 0.70}])
    sim = simulate_kelly(bets, initial_bankroll=1000.0, kelly_fraction=0.25,
                         max_stake_pct=0.05, max_daily_exposure_pct=0.10)
    assert sim["ledger"].iloc[0]["pnl"] == 0.0
    assert abs(sim["total_profit"]) < 1e-9
