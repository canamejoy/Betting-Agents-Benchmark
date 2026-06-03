"""Performance and risk metrics."""

import math
import pandas as pd


def compute_betting_metrics(results_df: pd.DataFrame, runtime: float) -> dict:
    if results_df.empty:
        return _empty_betting(runtime)

    total_staked = results_df["stake"].sum()
    total_profit = results_df["pnl"].sum()
    roi = total_profit / total_staked if total_staked > 0 else 0.0

    settled = results_df[results_df["result"].isin(["win", "loss"])]
    hit_rate = (settled["result"] == "win").mean() if len(settled) > 0 else 0.0

    return {
        "total_profit": round(float(total_profit), 4),
        "roi": round(float(roi), 4),
        "total_staked": round(float(total_staked), 4),
        "hit_rate": round(float(hit_rate), 4),
        "bet_count": int(len(results_df)),
        "runtime_seconds": round(float(runtime), 2),
    }


def compute_risk_metrics(results_df: pd.DataFrame, max_drawdown: float, daily_staked: dict = None) -> dict:
    if results_df.empty:
        return _empty_risk()

    pnl = results_df["pnl"]
    profit_volatility = float(pnl.std()) if len(pnl) > 1 else 0.0
    mean_pnl = float(pnl.mean())
    sharpe = mean_pnl / profit_volatility if profit_volatility > 0 else 0.0

    max_stake = float(results_df["stake"].max())
    max_daily_exposure = max(daily_staked.values()) if daily_staked else float(results_df["stake"].max())

    initial_bankroll = results_df["bankroll"].iloc[0] - results_df["pnl"].iloc[0] + results_df["stake"].iloc[0]
    ruin_threshold = initial_bankroll * 0.20
    ruin_proxy = float((results_df["bankroll"] < ruin_threshold).mean())

    return {
        "max_drawdown": round(float(max_drawdown), 4),
        "profit_volatility": round(profit_volatility, 4),
        "sharpe_like_ratio": round(sharpe, 4),
        "max_stake": round(max_stake, 4),
        "max_daily_exposure": round(max_daily_exposure, 4),
        "risk_of_ruin_proxy": round(ruin_proxy, 4),
    }


def _empty_betting(runtime: float) -> dict:
    return {
        "total_profit": 0.0,
        "roi": 0.0,
        "total_staked": 0.0,
        "hit_rate": 0.0,
        "bet_count": 0,
        "runtime_seconds": round(float(runtime), 2),
    }


def _empty_risk() -> dict:
    return {
        "max_drawdown": 0.0,
        "profit_volatility": 0.0,
        "sharpe_like_ratio": 0.0,
        "max_stake": 0.0,
        "max_daily_exposure": 0.0,
        "risk_of_ruin_proxy": 0.0,
    }
