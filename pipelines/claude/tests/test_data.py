import pandas as pd
import pytest
from pathlib import Path

from src.data import load_data, chronological_split

DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "sample_betting_data.csv"


def test_load_data_returns_dataframe():
    df = load_data(DATA_PATH)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 70


def test_load_data_sorted_by_date():
    df = load_data(DATA_PATH)
    assert df["event_date"].is_monotonic_increasing


def test_load_data_valid_results():
    df = load_data(DATA_PATH)
    assert set(df["result"].unique()).issubset({"win", "loss", "push"})


def test_load_data_missing_column(tmp_path):
    # Provide event_date so parse_dates doesn't fail first, but omit required 'sport'
    csv = tmp_path / "bad.csv"
    pd.DataFrame({
        "event_id": [1], "event_date": ["2024-01-01"], "result": ["win"],
        "home_team": ["A"], "away_team": ["B"], "market": ["moneyline"],
        "selection": ["A"], "odds_decimal": [2.0], "closing_odds_decimal": [1.9],
    }).to_csv(csv, index=False)
    with pytest.raises(ValueError, match="Missing columns"):
        load_data(csv)


def test_chronological_split_sizes():
    df = load_data(DATA_PATH)
    train, test = chronological_split(df, 0.70)
    assert len(train) == 49
    assert len(test) == 21
    assert len(train) + len(test) == len(df)


def test_chronological_split_no_leakage():
    df = load_data(DATA_PATH)
    train, test = chronological_split(df, 0.70)
    assert train["event_date"].max() <= test["event_date"].min()
