import pandas as pd


def compute_ev(model_prob: float, odds_decimal: float) -> float:
    return (model_prob * odds_decimal) - 1.0


def add_ev(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ev"] = df["model_prob"] * df["odds_decimal"] - 1.0
    return df


def select_bets(df: pd.DataFrame, ev_threshold: float = 0.05) -> pd.DataFrame:
    return df[df["ev"] > ev_threshold].copy().reset_index(drop=True)
