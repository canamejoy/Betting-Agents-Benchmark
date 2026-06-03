"""Chronological backtest simulation."""

import pandas as pd

from .risk import (
    flat_stake,
    kelly_stake,
    apply_daily_exposure_cap,
    update_bankroll,
)


def run_flat(bets: pd.DataFrame, stake_amount: float, initial_bankroll: float):
    records = []
    bankroll = initial_bankroll
    peak = bankroll
    max_drawdown = 0.0

    for _, row in bets.iterrows():
        stake = flat_stake(stake_amount)
        result = row["result"]
        pnl = _pnl(stake, result, row["odds_decimal"])
        bankroll = max(0.0, bankroll + pnl)

        if bankroll > peak:
            peak = bankroll
        drawdown = (peak - bankroll) / peak if peak > 0 else 0.0
        max_drawdown = max(max_drawdown, drawdown)

        records.append(_record(row, stake, pnl, bankroll))

    return pd.DataFrame(records), max_drawdown


def run_kelly(
    bets: pd.DataFrame,
    initial_bankroll: float,
    kelly_fraction: float,
    max_stake_pct: float,
    max_daily_exposure_pct: float,
):
    records = []
    bankroll = initial_bankroll
    peak = bankroll
    max_drawdown = 0.0
    daily_staked: dict = {}

    for _, row in bets.iterrows():
        stake = kelly_stake(
            row["model_prob"],
            row["odds_decimal"],
            bankroll,
            kelly_fraction,
            max_stake_pct,
        )
        stake = apply_daily_exposure_cap(
            stake,
            row["event_date"],
            daily_staked,
            bankroll,
            max_daily_exposure_pct,
        )

        date_key = str(row["event_date"])
        daily_staked[date_key] = daily_staked.get(date_key, 0.0) + stake

        result = row["result"]
        pnl = _pnl(stake, result, row["odds_decimal"])
        bankroll = update_bankroll(bankroll, stake, result, row["odds_decimal"])

        if bankroll > peak:
            peak = bankroll
        drawdown = (peak - bankroll) / peak if peak > 0 else 0.0
        max_drawdown = max(max_drawdown, drawdown)

        records.append(_record(row, stake, pnl, bankroll))

    return pd.DataFrame(records), max_drawdown, daily_staked


def _pnl(stake: float, result: str, odds_decimal: float) -> float:
    if result == "win":
        return stake * (odds_decimal - 1.0)
    elif result == "loss":
        return -stake
    return 0.0  # push


def _record(row, stake: float, pnl: float, bankroll: float) -> dict:
    return {
        "event_id": row["event_id"],
        "event_date": row["event_date"],
        "result": row["result"],
        "odds_decimal": row["odds_decimal"],
        "model_prob": row.get("model_prob", None),
        "ev": row.get("ev", None),
        "stake": stake,
        "pnl": pnl,
        "bankroll": bankroll,
    }
