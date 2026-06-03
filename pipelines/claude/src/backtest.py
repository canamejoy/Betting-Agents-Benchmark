from typing import Any, Dict
import pandas as pd

from .risk import kelly_stake, cap_stake


def _settle(result: str, stake: float, odds_decimal: float) -> float:
    if result == "win":
        return stake * (odds_decimal - 1.0)
    elif result == "loss":
        return -stake
    else:  # push — stake returned, net pnl = 0
        return 0.0


def simulate_flat(bets_df: pd.DataFrame, flat_stake: float = 1.0) -> Dict[str, Any]:
    """Chronological flat-stake backtest."""
    rows = []
    bankroll = 0.0
    total_stake = 0.0
    peak = 0.0
    max_drawdown = 0.0

    for _, bet in bets_df.sort_values("event_date").iterrows():
        stake = flat_stake
        result = bet["result"]
        pnl = _settle(result, stake, bet["odds_decimal"])

        bankroll += pnl
        total_stake += stake
        peak = max(peak, bankroll)
        max_drawdown = max(max_drawdown, peak - bankroll)

        rows.append({
            "event_id": bet["event_id"],
            "event_date": bet["event_date"],
            "result": result,
            "stake": stake,
            "pnl": pnl,
            "bankroll": bankroll,
        })

    _empty_cols = ["event_id", "event_date", "result", "stake", "pnl", "bankroll"]
    ledger = pd.DataFrame(rows) if rows else pd.DataFrame(columns=_empty_cols)
    return {
        "ledger": ledger,
        "total_profit": bankroll,
        "total_stake": total_stake,
        "max_drawdown": max_drawdown,
    }


def simulate_kelly(
    bets_df: pd.DataFrame,
    initial_bankroll: float = 1000.0,
    kelly_fraction: float = 0.25,
    max_stake_pct: float = 0.05,
    max_daily_exposure_pct: float = 0.10,
) -> Dict[str, Any]:
    """Chronological Kelly-fraction backtest with stake and daily exposure caps."""
    rows = []
    bankroll = initial_bankroll
    total_stake = 0.0
    peak = initial_bankroll
    max_drawdown = 0.0
    daily_exposure: Dict[str, float] = {}

    for _, bet in bets_df.sort_values("event_date").iterrows():
        date_key = str(bet["event_date"])[:10]

        stake = kelly_stake(bet["model_prob"], bet["odds_decimal"], kelly_fraction, bankroll)
        stake = cap_stake(stake, bankroll, max_stake_pct)

        day_used = daily_exposure.get(date_key, 0.0)
        max_day = bankroll * max_daily_exposure_pct
        stake = min(stake, max(0.0, max_day - day_used))

        if stake <= 0:
            continue

        daily_exposure[date_key] = day_used + stake
        result = bet["result"]
        pnl = _settle(result, stake, bet["odds_decimal"])
        bankroll += pnl
        total_stake += stake
        peak = max(peak, bankroll)
        max_drawdown = max(max_drawdown, peak - bankroll)

        rows.append({
            "event_id": bet["event_id"],
            "event_date": bet["event_date"],
            "result": result,
            "stake": round(stake, 4),
            "pnl": round(pnl, 4),
            "bankroll": round(bankroll, 4),
        })

    _empty_cols = ["event_id", "event_date", "result", "stake", "pnl", "bankroll"]
    ledger = pd.DataFrame(rows) if rows else pd.DataFrame(columns=_empty_cols)
    return {
        "ledger": ledger,
        "total_profit": bankroll - initial_bankroll,
        "total_stake": total_stake,
        "max_drawdown": max_drawdown,
        "final_bankroll": bankroll,
        "initial_bankroll": initial_bankroll,
        "daily_exposure": daily_exposure,
    }
