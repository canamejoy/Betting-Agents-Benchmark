"""Experiment 03 — Fixed broken pipeline with regression tests.

Bugs found in the original broken_pipeline/pipeline.py:

  Bug 1: compute_implied_probability used odds/(1+odds) instead of 1/odds.
    This inflates implied probabilities, underestimates edge, and causes bad
    EV calculations. Fixed: return 1.0 / odds_decimal.

  Bug 2: ROI was computed as total_profit / len(results_df) (divides by bet
    count) instead of total_profit / total_stake. ROI must be return per unit
    staked, not per bet.  Fixed: roi = total_profit / total_stake.

  Bug 3: Push results were treated as losses (pnl = -stake). Pushes should
    return the stake; pnl must be 0. Fixed: added push branch to pnl logic.
"""

import json
import time
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder

RUNS_DIR = Path(__file__).resolve().parents[1] / "runs" / "experiment_03"

CONFIG = {
    "data_path": Path(__file__).resolve().parents[3] / "data" / "sample_betting_data.csv",
    "train_ratio": 0.70,
    "ev_threshold": 0.05,
    "flat_stake": 1.0,
    "initial_bankroll": 1000.0,
}


def load_data(path):
    df = pd.read_csv(path, parse_dates=["event_date"])
    df = df.sort_values("event_date").reset_index(drop=True)
    required = [
        "event_id", "event_date", "sport", "home_team", "away_team",
        "market", "selection", "odds_decimal", "result",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    return df


def compute_implied_probability(odds_decimal):
    # BUG FIX: was odds_decimal / (1 + odds_decimal) — wrong formula.
    return 1.0 / odds_decimal


def build_features(df):
    enc_sport = LabelEncoder()
    enc_market = LabelEncoder()
    df = df.copy()
    df["implied_prob"] = df["odds_decimal"].apply(compute_implied_probability)
    df["sport_enc"] = enc_sport.fit_transform(df["sport"])
    df["market_enc"] = enc_market.fit_transform(df["market"])
    df["is_home"] = (df["selection"] == df["home_team"]).astype(int)
    return df


def train_model(train_df):
    features = ["implied_prob", "sport_enc", "market_enc", "is_home"]
    X = train_df[features].values
    y = (train_df["result"] == "win").astype(int).values
    model = LogisticRegression(max_iter=500, random_state=42)
    model.fit(X, y)
    return model


def predict_and_select(df, model, threshold):
    features = ["implied_prob", "sport_enc", "market_enc", "is_home"]
    probs = model.predict_proba(df[features].values)[:, 1]
    df = df.copy()
    df["model_prob"] = probs
    df["ev"] = (df["model_prob"] * df["odds_decimal"]) - 1
    return df[df["ev"] > threshold].copy()


def simulate_backtest(bets, stake):
    records = []
    bankroll = CONFIG["initial_bankroll"]
    peak = bankroll
    max_drawdown = 0.0

    for _, row in bets.iterrows():
        result = row["result"]

        # BUG FIX: push was previously treated as loss (pnl = -stake).
        if result == "win":
            pnl = stake * (row["odds_decimal"] - 1)
        elif result == "loss":
            pnl = -stake
        else:  # push — stake returned, no profit/loss
            pnl = 0.0

        bankroll += pnl
        if bankroll > peak:
            peak = bankroll
        drawdown = (peak - bankroll) / peak if peak > 0 else 0
        if drawdown > max_drawdown:
            max_drawdown = drawdown

        records.append({
            "event_id": row["event_id"],
            "result": result,
            "stake": stake,
            "pnl": pnl,
            "bankroll": bankroll,
        })

    return pd.DataFrame(records), max_drawdown


def compute_metrics(bets_df, results_df, max_drawdown, runtime):
    total_stake = results_df["stake"].sum()
    total_profit = results_df["pnl"].sum()

    # BUG FIX: was total_profit / len(results_df) — divides by bet count,
    # not by total staked. ROI = profit / staked.
    roi = total_profit / total_stake if total_stake > 0 else 0.0

    settled = results_df[results_df["result"].isin(["win", "loss"])]
    hit_rate = (settled["result"] == "win").mean() if len(settled) > 0 else 0.0

    return {
        "total_profit": round(float(total_profit), 4),
        "roi": round(float(roi), 4),
        "total_staked": round(float(total_stake), 4),
        "hit_rate": round(float(hit_rate), 4),
        "bet_count": int(len(results_df)),
        "max_drawdown": round(float(max_drawdown), 4),
        "runtime_seconds": round(float(runtime), 2),
    }


def run():
    t0 = time.time()

    df = load_data(CONFIG["data_path"])
    df = build_features(df)

    split_idx = int(len(df) * CONFIG["train_ratio"])
    train_df = df.iloc[:split_idx]
    eval_df = df.iloc[split_idx:]

    model = train_model(train_df)
    bets = predict_and_select(eval_df, model, CONFIG["ev_threshold"])

    results_df, max_drawdown = simulate_backtest(bets, CONFIG["flat_stake"])
    runtime = time.time() - t0

    metrics = compute_metrics(bets, results_df, max_drawdown, runtime)
    print(json.dumps(metrics, indent=2))

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RUNS_DIR / "metrics.json"
    with open(out_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved to {out_path}")

    return metrics


if __name__ == "__main__":
    run()
