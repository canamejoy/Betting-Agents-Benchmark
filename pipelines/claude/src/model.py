import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from .features import FEATURE_COLS


def train_model(train_df: pd.DataFrame) -> LogisticRegression:
    X = train_df[FEATURE_COLS]
    y = (train_df["result"] == "win").astype(int)
    clf = LogisticRegression(random_state=42, max_iter=1000)
    clf.fit(X, y)
    return clf


def predict_win_prob(clf: LogisticRegression, df: pd.DataFrame) -> np.ndarray:
    return clf.predict_proba(df[FEATURE_COLS])[:, 1]
