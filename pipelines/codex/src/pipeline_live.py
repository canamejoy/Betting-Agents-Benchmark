"""Live betting pipeline — fetches real odds, scores them, and places bets.

Usage:
  python pipelines/codex/run_live.py           # dry-run (no real bets)
  python pipelines/codex/run_live.py --live    # live mode (real bets on Stake.com)
"""

import json
import logging
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from .config import LIVE as _DEFAULT_CFG
from .data import load_data, chronological_split
from .features import FeaturePipeline
from .model import BettingModel
from .betting import select_bets
from .risk import kelly_stake, apply_daily_exposure_cap
from .live_data import fetch_odds, parse_odds_response, SPORT_MAP
from .browser_bettor import BrowserBettor
import os
from .reporting import save_metrics

logger = logging.getLogger(__name__)
RUNS_DIR = Path(__file__).resolve().parents[1] / "runs" / "live"
LIVE_SPORTS = list(SPORT_MAP.keys())[:2]  # limit to 2 sports to reduce API usage


def _train_model(cfg: dict):
    """Train model on historical data."""
    df = load_data(cfg["data_path"])
    train_df, _ = chronological_split(df, cfg["train_ratio"])

    fp = FeaturePipeline()
    train_df = fp.fit_transform(train_df)

    model = BettingModel(random_state=cfg["random_state"])
    model.fit(train_df)
    return model, fp


def _score_live_rows(rows: list, model: BettingModel, fp: FeaturePipeline, cfg: dict) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["odds_decimal"] = pd.to_numeric(df["odds_decimal"], errors="coerce")
    df = df.dropna(subset=["odds_decimal"])
    df = df[df["odds_decimal"] > 1.0]
    if df.empty:
        return df
    df = fp.transform(df)
    probs = model.predict_proba(df)
    return select_bets(df, probs, cfg["ev_threshold"])


def run(live: bool = False, cfg: dict = None) -> dict:
    cfg = cfg or _DEFAULT_CFG
    if live:
        cfg = {**cfg, "dry_run": False}

    if not cfg["dry_run"]:
        confirm = input("Type YES to confirm live betting on Stake.com: ")
        if confirm.strip() != "YES":
            print("Aborted.")
            return {}

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    t0 = time.time()

    if not cfg["odds_api_key"]:
        raise RuntimeError("ODDS_API_KEY is not set. Provide it in .env or as an environment variable.")

    logger.info("Training model on historical data …")
    model, fp = _train_model(cfg)

    logger.info("Fetching live odds …")
    all_rows = []
    for sport_key in LIVE_SPORTS:
        try:
            games = fetch_odds(cfg["odds_api_key"], sport_key)
            rows = parse_odds_response(games, SPORT_MAP[sport_key])
            all_rows.extend(rows)
            logger.info("Fetched %d rows for %s", len(rows), sport_key)
        except Exception as exc:
            logger.warning("Could not fetch odds for %s: %s", sport_key, exc)

    bets = _score_live_rows(all_rows, model, fp, cfg)
    logger.info("Selected %d bets above EV threshold", len(bets))

    bankroll = cfg["initial_bankroll"]
    cop_to_usd = cfg["cop_to_usd"]
    bet_records = []
    daily_staked: dict = {}

    with BrowserBettor(
        email=cfg["stake_email"],
        password=cfg["stake_password"],
        dry_run=cfg["dry_run"],
    ) as bettor:
        for _, row in bets.iterrows():
            stake_cop = kelly_stake(
                row["model_prob"],
                row["odds_decimal"],
                bankroll,
                cfg["kelly_fraction"],
                cfg["max_stake_pct"],
            )
            stake_cop = apply_daily_exposure_cap(
                stake_cop,
                row["event_date"],
                daily_staked,
                bankroll,
                0.10,
            )
            date_key = str(row["event_date"])
            daily_staked[date_key] = daily_staked.get(date_key, 0.0) + stake_cop

            stake_usd = stake_cop * cop_to_usd
            if stake_usd < 0.01:
                continue

            result = bettor.place_bet(
                row["selection"],
                row["odds_decimal"],
                stake_usd,
                home_team=row.get("home_team", ""),
                away_team=row.get("away_team", ""),
            )
            bet_records.append({
                **result,
                "event_id": row.get("event_id"),
                "event_date": row.get("event_date"),
                "ev": row.get("ev"),
                "model_prob": row.get("model_prob"),
                "stake_cop": stake_cop,
            })

    runtime = time.time() - t0
    report = {
        "mode": "live" if not cfg["dry_run"] else "dry_run",
        "bets_selected": len(bets),
        "bets_attempted": len(bet_records),
        "runtime_seconds": round(runtime, 2),
        "bet_records": bet_records,
    }

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = RUNS_DIR / "live_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info("Report saved to %s", report_path)

    return report
