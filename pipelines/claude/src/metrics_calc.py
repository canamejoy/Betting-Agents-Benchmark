from typing import Any, Dict
import numpy as np
import pandas as pd


def betting_metrics(sim: Dict[str, Any], runtime: float) -> Dict[str, Any]:
    ledger: pd.DataFrame = sim["ledger"]
    total_profit = sim["total_profit"]
    total_stake = sim["total_stake"]
    max_drawdown = sim["max_drawdown"]

    bet_count = len(ledger)
    non_push = ledger[ledger["result"] != "push"] if bet_count > 0 else ledger
    wins = (non_push["result"] == "win").sum() if len(non_push) > 0 else 0

    hit_rate = int(wins) / len(non_push) if len(non_push) > 0 else 0.0
    roi = total_profit / total_stake if total_stake > 0 else 0.0

    return {
        "total_profit": round(float(total_profit), 4),
        "roi": round(float(roi), 4),
        "hit_rate": round(float(hit_rate), 4),
        "bet_count": int(bet_count),
        "max_drawdown": round(float(max_drawdown), 4),
        "runtime_seconds": round(float(runtime), 3),
    }


def risk_metrics(sim: Dict[str, Any], runtime: float) -> Dict[str, Any]:
    base = betting_metrics(sim, runtime)
    ledger: pd.DataFrame = sim["ledger"]

    pnls = ledger["pnl"].values if len(ledger) > 0 else np.array([])

    if len(pnls) > 1:
        profit_volatility = float(np.std(pnls, ddof=1))
        mean_pnl = float(np.mean(pnls))
        sharpe_like = mean_pnl / profit_volatility if profit_volatility > 0 else 0.0
    else:
        profit_volatility = 0.0
        sharpe_like = 0.0

    max_stake = float(ledger["stake"].max()) if len(ledger) > 0 else 0.0

    if len(ledger) > 0:
        tmp = ledger.copy()
        tmp["date"] = pd.to_datetime(tmp["event_date"]).dt.date
        max_daily_exposure = float(tmp.groupby("date")["stake"].sum().max())
    else:
        max_daily_exposure = 0.0

    initial_bankroll = sim.get("initial_bankroll", sim.get("total_stake", 1.0))
    final_bankroll = sim.get("final_bankroll", initial_bankroll + sim["total_profit"])
    risk_of_ruin_proxy = float(sim["max_drawdown"] / initial_bankroll) if initial_bankroll > 0 else 0.0

    return {
        **base,
        "profit_volatility": round(profit_volatility, 4),
        "sharpe_like_ratio": round(sharpe_like, 4),
        "max_stake": round(max_stake, 4),
        "max_daily_exposure": round(max_daily_exposure, 4),
        "risk_of_ruin_proxy": round(risk_of_ruin_proxy, 4),
        "final_bankroll": round(float(final_bankroll), 4),
    }
