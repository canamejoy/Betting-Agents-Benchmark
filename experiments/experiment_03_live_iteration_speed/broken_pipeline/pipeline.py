"""
Broken baseline betting pipeline for Experiment 03.

This file contains intentional bugs. Do not use it as a reference implementation.
Copy it to pipelines/<your-tool>/src/ and fix it there.
"""

import json
import time

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder


CONFIG = {
    "data_path": "data/sample_betting_data.csv",
    "train_ratio": 0.70,
    "ev_threshold": 0.05,
    "flat_stake": 1.0,
    "initial_bankroll": 1000.0,
}


def load_data(path):
    df = pd.read_csv(path, parse_dates=["event_date"])
    df = df.sort_values("event_date").reset_index(drop=True)
    required = [
        "event_id",
        "event_date",
        "sport",
        "home_team",
        "away_team",
        "market",
        "selection",
        "odds_decimal",
        "result",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    return df


def compute_implied_probability(odds_decimal):
    return odds_decimal / (1 + odds_decimal)


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
    model = LogisticRegression(max_iter=500)
    model.fit(X, y)
    return model


def predict_and_select(df, model, threshold):
    features = ["implied_prob", "sport_enc", "market_enc", "is_home"]
    probs = model.predict_proba(df[features].values)[:, 1]
    df = df.copy()
    df["model_prob"] = probs
    df["ev"] = (df["model_prob"] * df["odds_decimal"]) - 1
    bets = df[df["ev"] > threshold].copy()
    return bets


def simulate_backtest(bets, stake):
    records = []
    bankroll = CONFIG["initial_bankroll"]
    peak = bankroll
    max_drawdown = 0.0

    for _, row in bets.iterrows():
        result = row["result"]

        if result == "win":
            pnl = stake * (row["odds_decimal"] - 1)
        else:
            pnl = -stake

        bankroll += pnl
        if bankroll > peak:
            peak = bankroll
        drawdown = (peak - bankroll) / peak if peak > 0 else 0
        if drawdown > max_drawdown:
            max_drawdown = drawdown

        records.append(
            {
                "event_id": row["event_id"],
                "result": result,
                "stake": stake,
                "pnl": pnl,
                "bankroll": bankroll,
            }
        )

    return pd.DataFrame(records), max_drawdown


def compute_metrics(bets_df, results_df, max_drawdown, runtime):
    total_stake = results_df["stake"].sum()
    total_profit = results_df["pnl"].sum()
    roi = total_profit / len(results_df) if len(results_df) > 0 else 0.0

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

    with open("metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics


if __name__ == "__main__":
    run()
