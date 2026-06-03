"""
Experiment 03 — Fixed pipeline (started from broken_pipeline/pipeline.py).

Bugs found and fixed:
  BUG 1 — compute_implied_probability returned odds/(1+odds) instead of 1/odds.
           A fair-odds implied prob is always 1/decimal_odds.
           Wrong formula produced values ~0.60 for odds 1.5 instead of the correct ~0.67.

  BUG 2 — simulate_backtest used a bare `else: pnl = -stake`, so pushes were
           settled as losses. A push returns the stake (net pnl = 0).

  BUG 3 — compute_metrics divided total_profit by len(results_df) (bet count)
           instead of total_stake. ROI must be profit / total_staked.

Secondary fix: build_features was called on the full dataset before the
train/test split, fitting the LabelEncoder on test-set categories. Moved
feature engineering to after the split with encoders fit only on train data.
"""

import json
import logging
import time
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder

from .config import EXPERIMENT_03 as CFG

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

CONFIG = {
    "data_path": str(CFG["data_path"]),
    "train_ratio": CFG["train_ratio"],
    "ev_threshold": CFG["ev_threshold"],
    "flat_stake": CFG["flat_stake"],
    "initial_bankroll": 1000.0,
}


def load_data(path):
    df = pd.read_csv(path, parse_dates=["event_date"])
    df = df.sort_values("event_date").reset_index(drop=True)
    required = ["event_id", "event_date", "sport", "home_team", "away_team",
                "market", "selection", "odds_decimal", "result"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    return df


def compute_implied_probability(odds_decimal):
    # FIX BUG 1: was `odds_decimal / (1 + odds_decimal)` — wrong formula.
    return 1.0 / odds_decimal


def build_features(train_df, eval_df):
    # FIX secondary: fit encoders on train only, then apply to eval.
    enc_sport = LabelEncoder()
    enc_market = LabelEncoder()
    enc_sport.fit(train_df["sport"])
    enc_market.fit(train_df["market"])

    def _transform(df):
        df = df.copy()
        df["implied_prob"] = df["odds_decimal"].apply(compute_implied_probability)
        df["sport_enc"] = enc_sport.transform(df["sport"])
        df["market_enc"] = enc_market.transform(df["market"])
        df["is_home"] = (df["selection"] == df["home_team"]).astype(int)
        return df

    return _transform(train_df), _transform(eval_df)


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

        if result == "win":
            pnl = stake * (row["odds_decimal"] - 1)
        elif result == "loss":
            pnl = -stake
        else:
            # FIX BUG 2: push returns the stake (net pnl = 0), not -stake.
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


def compute_metrics(results_df, max_drawdown, runtime):
    total_stake = results_df["stake"].sum()
    total_profit = results_df["pnl"].sum()

    # FIX BUG 3: was `total_profit / len(results_df)` — divided by count, not staked.
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
    log.info("=== Experiment 03: Fixed Pipeline ===")

    df = load_data(CONFIG["data_path"])
    split_idx = int(len(df) * CONFIG["train_ratio"])
    train_df = df.iloc[:split_idx].copy()
    eval_df = df.iloc[split_idx:].copy()
    log.info("Split: train=%d  eval=%d", len(train_df), len(eval_df))

    train_df, eval_df = build_features(train_df, eval_df)
    model = train_model(train_df)

    bets = predict_and_select(eval_df, model, CONFIG["ev_threshold"])
    log.info("Bets selected: %d", len(bets))

    results_df, max_drawdown = simulate_backtest(bets, CONFIG["flat_stake"])
    runtime = time.time() - t0

    metrics = compute_metrics(results_df, max_drawdown, runtime)
    log.info("Results: %s", metrics)

    out = CFG["output_dir"]
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    results_df.to_csv(out / "ledger.csv", index=False)
    log.info("Saved to %s", out)
    return metrics


if __name__ == "__main__":
    run()
