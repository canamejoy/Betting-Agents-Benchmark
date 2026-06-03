"""Central configuration for all experiments."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "data" / "sample_betting_data.csv"

EXPERIMENT_01 = {
    "data_path": DATA_PATH,
    "train_ratio": 0.70,
    "ev_threshold": 0.05,
    "flat_stake": 1.0,
    "initial_bankroll": 1000.0,
    "random_state": 42,
}

EXPERIMENT_02 = {
    **EXPERIMENT_01,
    "kelly_fraction": 0.25,
    "max_stake_pct": 0.05,
    "max_daily_exposure_pct": 0.10,
}

LIVE = {
    "data_path": DATA_PATH,
    "ev_threshold": float(os.getenv("LIVE_EV_THRESHOLD", "0.05")),
    "kelly_fraction": float(os.getenv("LIVE_KELLY_FRACTION", "0.25")),
    "max_stake_pct": float(os.getenv("LIVE_MAX_STAKE_PCT", "0.05")),
    "initial_bankroll": float(os.getenv("LIVE_BANKROLL", "10000")),
    "cop_to_usd": float(os.getenv("COP_TO_USD_RATE", "0.00025")),
    "dry_run": os.getenv("DRY_RUN", "true").lower() == "true",
    "odds_api_key": os.getenv("ODDS_API_KEY", ""),
    "stake_email": os.getenv("STAKE_EMAIL", ""),
    "stake_password": os.getenv("STAKE_PASSWORD", ""),
    "train_ratio": 0.70,
    "random_state": 42,
}
