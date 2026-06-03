"""Probability estimation using logistic regression."""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from .features import FEATURE_COLS


class BettingModel:
    def __init__(self, random_state: int = 42):
        self._model = LogisticRegression(max_iter=1000, random_state=random_state)

    def fit(self, train_df: pd.DataFrame) -> None:
        X = train_df[FEATURE_COLS].values
        y = (train_df["result"] == "win").astype(int).values
        self._model.fit(X, y)

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        X = df[FEATURE_COLS].values
        return self._model.predict_proba(X)[:, 1]
