import pandas as pd
import pytest

from src.features import FeatureEncoder, FEATURE_COLS


def _make_df(n=10):
    return pd.DataFrame({
        "event_id": range(n),
        "odds_decimal": [1.5, 2.0, 2.5, 1.8, 3.0, 1.9, 2.2, 1.6, 2.8, 1.4],
        "home_team": ["A"] * n,
        "away_team": ["B"] * n,
        "selection": (["A"] * 5) + (["B"] * 5),
        "sport": ["soccer"] * 4 + ["basketball"] * 4 + ["tennis"] * 2,
        "market": ["moneyline"] * 6 + ["spread"] * 4,
        "result": ["win", "loss", "push"] * 3 + ["win"],
    })


def test_implied_prob_correct():
    df = _make_df()
    enc = FeatureEncoder()
    out = enc.fit_transform(df)
    assert abs(out.iloc[0]["implied_prob"] - 1 / 1.5) < 1e-9


def test_is_home_flag():
    df = _make_df()
    enc = FeatureEncoder()
    out = enc.fit_transform(df)
    assert out.iloc[0]["is_home"] == 1   # selection == home_team
    assert out.iloc[5]["is_home"] == 0   # selection == away_team


def test_feature_cols_present():
    df = _make_df()
    enc = FeatureEncoder()
    out = enc.fit_transform(df)
    for col in FEATURE_COLS:
        assert col in out.columns


def test_encoder_consistent_train_test():
    df = _make_df()
    train = df.iloc[:7]
    test = df.iloc[7:]
    enc = FeatureEncoder()
    train_out = enc.fit_transform(train)
    test_out = enc.transform(test)
    # "basketball" appears in both train (rows 4-6) and test (row 7): codes must match
    train_code = train_out[train_out["sport"] == "basketball"]["sport_encoded"].iloc[0]
    test_code = test_out[test_out["sport"] == "basketball"]["sport_encoded"].iloc[0]
    assert train_code == test_code
