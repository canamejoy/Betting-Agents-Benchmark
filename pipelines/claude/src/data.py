from pathlib import Path
import pandas as pd

_REQUIRED_COLS = {
    "event_id", "event_date", "sport", "home_team", "away_team",
    "market", "selection", "odds_decimal", "closing_odds_decimal", "result",
}
_VALID_RESULTS = {"win", "loss", "push"}


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["event_date"])
    missing = _REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    invalid = set(df["result"].unique()) - _VALID_RESULTS
    if invalid:
        raise ValueError(f"Unexpected result values: {invalid}")
    return df.sort_values("event_date").reset_index(drop=True)


def chronological_split(df: pd.DataFrame, train_ratio: float = 0.70):
    n = int(len(df) * train_ratio)
    return df.iloc[:n].copy(), df.iloc[n:].copy()
