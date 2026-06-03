"""Data loading and validation."""

import pandas as pd

REQUIRED_COLUMNS = [
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

VALID_RESULTS = {"win", "loss", "push"}


def load_data(path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["event_date"])
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    invalid_odds = df["odds_decimal"] <= 1.0
    if invalid_odds.any():
        df = df[~invalid_odds].copy()

    invalid_results = ~df["result"].isin(VALID_RESULTS)
    if invalid_results.any():
        df = df[~invalid_results].copy()

    df = df.sort_values("event_date").reset_index(drop=True)
    return df


def chronological_split(df: pd.DataFrame, train_ratio: float):
    split_idx = int(len(df) * train_ratio)
    return df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()
