from dataclasses import dataclass, field
from typing import List
import pandas as pd

FEATURE_COLS = ["implied_prob", "is_home", "sport_encoded", "market_encoded"]


@dataclass
class FeatureEncoder:
    sport_cats: List[str] = field(default_factory=list)
    market_cats: List[str] = field(default_factory=list)

    def fit(self, df: pd.DataFrame) -> "FeatureEncoder":
        self.sport_cats = sorted(df["sport"].unique())
        self.market_cats = sorted(df["market"].unique())
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["implied_prob"] = 1.0 / df["odds_decimal"]
        df["is_home"] = (df["selection"] == df["home_team"]).astype(int)
        sport_map = {s: i for i, s in enumerate(self.sport_cats)}
        market_map = {m: i for i, m in enumerate(self.market_cats)}
        df["sport_encoded"] = df["sport"].map(sport_map).fillna(-1).astype(int)
        df["market_encoded"] = df["market"].map(market_map).fillna(-1).astype(int)
        return df

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.fit(df).transform(df)
