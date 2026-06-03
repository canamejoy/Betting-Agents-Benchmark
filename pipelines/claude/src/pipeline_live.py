"""
Live betting pipeline:
  1. Train logistic regression on historical CSV data.
  2. Fetch upcoming odds from The Odds API.
  3. Run the model on upcoming events to estimate win probabilities.
  4. Compute EV and select bets above the configured threshold.
  5. Place bets on Stake.com (or log them in dry-run mode).
  6. Save a run report.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from .config import LIVE as CFG
from .data import load_data, chronological_split
from .features import FeatureEncoder
from .model import train_model, predict_win_prob
from .betting import add_ev, select_bets
from .risk import kelly_stake, cap_stake
from .live_data import fetch_all_sports_df
from .live_bettor import StakeSession, BetResult
from .reporting import save_metrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Model training
# ---------------------------------------------------------------------------

def _train_on_history(cfg: Dict[str, Any]):
    """Train and return (encoder, clf) on the historical dataset."""
    df = load_data(cfg["historical_data_path"])
    train_df, _ = chronological_split(df, cfg["train_ratio"])
    encoder = FeatureEncoder()
    train_feats = encoder.fit_transform(train_df)
    clf = train_model(train_feats)
    log.info("Model trained on %d historical rows", len(train_df))
    return encoder, clf


# ---------------------------------------------------------------------------
# Score upcoming events
# ---------------------------------------------------------------------------

def _score_events(upcoming_df: pd.DataFrame, encoder: FeatureEncoder, clf, ev_threshold: float) -> pd.DataFrame:
    """
    Apply the trained model to upcoming events and return only positive-EV rows.
    Rows with missing features are dropped with a warning.
    """
    if upcoming_df.empty:
        log.warning("No upcoming events to score")
        return pd.DataFrame()

    feats = encoder.transform(upcoming_df)
    feats["model_prob"] = predict_win_prob(clf, feats)
    feats = add_ev(feats)
    bets = select_bets(feats, ev_threshold)
    log.info("Scored %d upcoming rows → %d positive-EV bets (EV > %.2f)",
             len(upcoming_df), len(bets), ev_threshold)
    return bets


# ---------------------------------------------------------------------------
# Stake sizing for live bets
# ---------------------------------------------------------------------------

def _size_stakes(bets: pd.DataFrame, bankroll: float, kelly_fraction: float, max_stake_pct: float) -> pd.DataFrame:
    """Add stake_cop column (in COP) to the bets DataFrame."""
    stakes = []
    for _, row in bets.iterrows():
        raw = kelly_stake(row["model_prob"], row["odds_decimal"], kelly_fraction, bankroll)
        capped = cap_stake(raw, bankroll, max_stake_pct)
        stakes.append(round(capped, 2))
    bets = bets.copy()
    bets["stake_cop"] = stakes
    # Drop bets that would be below Stake's $0.10 USD minimum (~400 COP at 4000 COP/USD).
    min_cop = 1.0 / CFG["cop_to_usd_rate"] * 0.10
    bets = bets[bets["stake_cop"] >= min_cop].reset_index(drop=True)
    log.info("%d bets survive the Stake $0.10 USD minimum stake filter", len(bets))
    return bets


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _save_live_report(bets: pd.DataFrame, results: List[BetResult], output_dir: Path, runtime: float) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    placed = [r for r in results if r.placed]
    failed = [r for r in results if not r.placed]
    total_stake = sum(r.stake_cop for r in placed)
    dry_run = any(r.dry_run for r in results)

    report: Dict[str, Any] = {
        "dry_run": dry_run,
        "bets_selected": len(bets),
        "bets_placed": len(placed),
        "bets_failed": len(failed),
        "total_stake_cop": round(total_stake, 2),
        "runtime_seconds": round(runtime, 3),
        "bets": [
            {
                "event_id": r.event_id,
                "selection": r.selection,
                "odds": r.odds,
                "stake_cop": r.stake_cop,
                "placed": r.placed,
                "error": r.error,
            }
            for r in results
        ],
    }

    out_path = output_dir / "live_report.json"
    out_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    log.info("Live report saved to %s", out_path)

    if not bets.empty:
        bets.to_csv(output_dir / "live_bets_selected.csv", index=False)

    return report


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run(dry_run: bool | None = None) -> Dict[str, Any]:
    t0 = time.time()

    effective_dry_run = CFG["dry_run"] if dry_run is None else dry_run
    log.info("=== Live Pipeline | dry_run=%s ===", effective_dry_run)

    # Validate credentials early.
    if not CFG["odds_api_key"]:
        raise ValueError("ODDS_API_KEY is not set. Copy .env.example to .env and fill in your key.")
    if not effective_dry_run and (not CFG["stake_email"] or not CFG["stake_password"]):
        raise ValueError("STAKE_EMAIL / STAKE_PASSWORD not set. Required when dry_run=false.")

    # Step 1: Train model on historical data.
    encoder, clf = _train_on_history(CFG)

    # Step 2: Fetch upcoming odds from The Odds API.
    log.info("Fetching upcoming odds for sports: %s", CFG["sports"])
    upcoming_df = fetch_all_sports_df(CFG["odds_api_key"], CFG["sports"], CFG["odds_regions"])
    if upcoming_df.empty:
        log.warning("No upcoming events found — nothing to bet on.")
        return {"bets_selected": 0, "bets_placed": 0}

    log.info("Fetched %d upcoming selection rows across %d events",
             len(upcoming_df), upcoming_df["event_id"].nunique())

    # Step 3: Score and select bets.
    bets = _score_events(upcoming_df, encoder, clf, CFG["ev_threshold"])
    if bets.empty:
        log.info("No positive-EV bets found this run.")
        return {"bets_selected": 0, "bets_placed": 0}

    # Step 4: Size stakes.
    bets = _size_stakes(bets, CFG["initial_bankroll"], CFG["kelly_fraction"], CFG["max_stake_pct"])
    if bets.empty:
        log.info("All bets fell below the Stake $0.10 USD minimum.")
        return {"bets_selected": 0, "bets_placed": 0}

    log.info("Selected bets:\n%s", bets[["event_id", "home_team", "away_team", "selection",
                                         "odds_decimal", "ev", "model_prob", "stake_cop"]].to_string(index=False))

    # Step 5: Place bets via Stake.com.
    results: List[BetResult] = []
    with StakeSession(
        email=CFG["stake_email"],
        password=CFG["stake_password"],
        dry_run=effective_dry_run,
        headless=False,  # keep headed so user can monitor / intervene
        cop_to_usd_rate=CFG["cop_to_usd_rate"],
    ) as session:
        if not effective_dry_run:
            logged_in = session.login()
            if not logged_in:
                log.error("Cannot proceed without a valid Stake login.")
                return {"error": "login_failed"}
        else:
            log.info("[DRY-RUN] Skipping Stake login")

        results = session.place_bets(bets, CFG["initial_bankroll"], CFG["max_stake_pct"])

    # Step 6: Save report.
    runtime = time.time() - t0
    report = _save_live_report(bets, results, Path(CFG["output_dir"]), runtime)
    placed = sum(1 for r in results if r.placed)
    log.info("Done | bets_selected=%d  bets_placed=%d  runtime=%.1fs", len(bets), placed, runtime)
    return report


if __name__ == "__main__":
    run()
