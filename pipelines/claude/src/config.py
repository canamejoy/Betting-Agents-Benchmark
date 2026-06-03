import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # loads .env from the repo root (or CWD)

_HERE = Path(__file__).resolve().parent        # pipelines/claude/src
_ROOT = _HERE.parents[2]                        # Betting-Agents-Benchmark/
_RUNS = _HERE.parent / "runs"                   # pipelines/claude/runs/

EXPERIMENT_01 = {
    "data_path": _ROOT / "data" / "sample_betting_data.csv",
    "train_ratio": 0.70,
    "ev_threshold": 0.05,
    "flat_stake": 1.0,
    "output_dir": _RUNS / "experiment_01",
}

EXPERIMENT_02 = {
    **EXPERIMENT_01,
    "initial_bankroll": 1000.0,
    "kelly_fraction": 0.25,
    "max_stake_pct": 0.05,
    "max_daily_exposure_pct": 0.10,
    "output_dir": _RUNS / "experiment_02",
}

EXPERIMENT_03 = {
    **EXPERIMENT_01,
    "output_dir": _RUNS / "experiment_03",
}

# Sports supported by The Odds API that Stake.com also covers.
# Full list: https://api.the-odds-api.com/v4/sports/?apiKey=...
_DEFAULT_SPORTS = [
    "soccer_colombia_primera_a",     # Liga BetPlay Dimayor
    "soccer_spain_la_liga",
    "soccer_england_league1",
    "soccer_epl",
    "basketball_nba",
]

LIVE = {
    "odds_api_key": os.getenv("ODDS_API_KEY", ""),
    "stake_email": os.getenv("STAKE_EMAIL", ""),
    "stake_password": os.getenv("STAKE_PASSWORD", ""),
    # COP to USD rate — 10 000 COP ≈ $2.50 USD at ~4000 COP/USD.
    # Update this value if the exchange rate changes significantly.
    "cop_to_usd_rate": float(os.getenv("COP_TO_USD_RATE", "0.00025")),
    "sports": _DEFAULT_SPORTS,
    "odds_regions": "eu",           # eu decimal odds
    "initial_bankroll": float(os.getenv("LIVE_BANKROLL", "10000")),
    "kelly_fraction": float(os.getenv("LIVE_KELLY_FRACTION", "0.25")),
    "max_stake_pct": float(os.getenv("LIVE_MAX_STAKE_PCT", "0.05")),
    "ev_threshold": float(os.getenv("LIVE_EV_THRESHOLD", "0.05")),
    "dry_run": os.getenv("DRY_RUN", "true").lower() == "true",
    # Total benchmark time in minutes; 10 min per experiment × 3 experiments = 30.
    "time_experiment_minutes": int(os.getenv("TIME_EXPERIMENT", "30")),
    "time_per_experiment_minutes": int(os.getenv("TIME_EXPERIMENT", "30")) // 3,
    "output_dir": _RUNS / "live",
    "historical_data_path": _ROOT / "data" / "sample_betting_data.csv",
    "train_ratio": 0.70,
}
