"""EV calculation and bet selection."""

import pandas as pd


def compute_ev(model_prob: float, odds_decimal: float) -> float:
    """Expected value per unit stake: (p * odds) - 1."""
    return (model_prob * odds_decimal) - 1.0


def select_bets(df: pd.DataFrame, model_probs, ev_threshold: float) -> pd.DataFrame:
    df = df.copy()
    df["model_prob"] = model_probs
    df["ev"] = df.apply(
        lambda r: compute_ev(r["model_prob"], r["odds_decimal"]), axis=1
    )
    return df[df["ev"] > ev_threshold].copy().reset_index(drop=True)
