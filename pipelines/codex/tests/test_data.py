"""Tests for data loading, validation, and chronological split."""

import pytest
import pandas as pd
import io
from pipelines.codex.src.data import load_data, chronological_split, REQUIRED_COLUMNS


SAMPLE_CSV = """event_id,event_date,sport,home_team,away_team,market,selection,odds_decimal,result
E001,2024-01-01,soccer,A,B,moneyline,A,2.0,win
E002,2024-01-02,soccer,C,D,moneyline,C,1.8,loss
E003,2024-01-03,basketball,E,F,moneyline,E,2.5,push
E004,2024-01-04,basketball,G,H,moneyline,G,1.5,win
"""


def _load_sample():
    from pathlib import Path
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(SAMPLE_CSV)
        path = f.name
    df = load_data(path)
    os.unlink(path)
    return df


def test_load_data_returns_sorted():
    df = _load_sample()
    assert list(df["event_date"]) == sorted(df["event_date"])


def test_load_data_raises_on_missing_column(tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("event_id,event_date\nE001,2024-01-01\n")
    with pytest.raises(ValueError, match="Missing columns"):
        load_data(bad_csv)


def test_chronological_split_ratio():
    df = _load_sample()
    train, eval_ = chronological_split(df, 0.75)
    assert len(train) == 3
    assert len(eval_) == 1


def test_no_overlap_in_split():
    df = _load_sample()
    train, eval_ = chronological_split(df, 0.50)
    assert set(train["event_id"]).isdisjoint(set(eval_["event_id"]))


def test_eval_dates_after_train():
    df = _load_sample()
    train, eval_ = chronological_split(df, 0.50)
    assert train["event_date"].max() <= eval_["event_date"].min()
