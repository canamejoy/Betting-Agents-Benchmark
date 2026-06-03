"""Feature engineering — all transformations are fit on train, applied to eval."""

import pandas as pd
from sklearn.preprocessing import LabelEncoder


def implied_probability(odds_decimal: float) -> float:
    """Convert decimal odds to implied probability: 1 / odds."""
    return 1.0 / odds_decimal


class FeaturePipeline:
    def __init__(self):
        self._sport_enc = LabelEncoder()
        self._market_enc = LabelEncoder()
        self._fitted = False

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["implied_prob"] = df["odds_decimal"].apply(implied_probability)
        df["sport_enc"] = self._sport_enc.fit_transform(df["sport"])
        df["market_enc"] = self._market_enc.fit_transform(df["market"])
        df["is_home"] = (df["selection"] == df["home_team"]).astype(int)
        self._fitted = True
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self._fitted:
            raise RuntimeError("Call fit_transform on training data first.")
        df = df.copy()
        df["implied_prob"] = df["odds_decimal"].apply(implied_probability)
        # handle unseen labels by mapping to -1 (treated as unknown)
        df["sport_enc"] = df["sport"].apply(self._safe_encode(self._sport_enc))
        df["market_enc"] = df["market"].apply(self._safe_encode(self._market_enc))
        df["is_home"] = (df["selection"] == df["home_team"]).astype(int)
        return df

    @staticmethod
    def _safe_encode(enc: LabelEncoder):
        known = set(enc.classes_)
        def _fn(val):
            return enc.transform([val])[0] if val in known else -1
        return _fn


FEATURE_COLS = ["implied_prob", "sport_enc", "market_enc", "is_home"]
