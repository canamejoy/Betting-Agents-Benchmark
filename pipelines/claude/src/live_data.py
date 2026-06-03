"""Fetch upcoming odds from The Odds API and convert to pipeline DataFrame format."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

import pandas as pd
import requests

log = logging.getLogger(__name__)

_BASE = "https://api.the-odds-api.com/v4"


def fetch_sports(api_key: str) -> List[Dict]:
    """Return all active sports available on The Odds API."""
    r = requests.get(f"{_BASE}/sports", params={"apiKey": api_key}, timeout=10)
    r.raise_for_status()
    return r.json()


def fetch_upcoming_odds(
    api_key: str,
    sport: str,
    regions: str = "eu",
    markets: str = "h2h",
) -> List[Dict[str, Any]]:
    """Fetch upcoming events with decimal h2h (moneyline) odds."""
    params = {
        "apiKey": api_key,
        "regions": regions,
        "markets": markets,
        "oddsFormat": "decimal",
        "dateFormat": "iso",
    }
    r = requests.get(f"{_BASE}/sports/{sport}/odds", params=params, timeout=15)
    if r.status_code == 422:
        log.warning("No upcoming events for sport '%s'", sport)
        return []
    r.raise_for_status()
    remaining = r.headers.get("x-requests-remaining", "?")
    log.info("Odds API: sport=%s  events=%d  requests_remaining=%s", sport, len(r.json()), remaining)
    return r.json()


def odds_to_dataframe(events: List[Dict[str, Any]], sport: str) -> pd.DataFrame:
    """
    Flatten Odds API events into the pipeline's row-per-selection schema.

    Each event produces two rows: one for each team (home and away moneyline).
    The `result` column is set to NaN — it will be filled after the event resolves.
    """
    rows = []
    for ev in events:
        home = ev.get("home_team", "")
        away = ev.get("away_team", "")
        event_date = pd.to_datetime(ev["commence_time"]).normalize()
        bookmakers = ev.get("bookmakers", [])
        if not bookmakers:
            continue

        # Use the first available bookmaker's h2h market.
        bk = bookmakers[0]
        markets = {m["key"]: m for m in bk.get("markets", [])}
        h2h = markets.get("h2h")
        if not h2h:
            continue

        outcomes = {o["name"]: o["price"] for o in h2h.get("outcomes", [])}
        home_odds = outcomes.get(home)
        away_odds = outcomes.get(away)

        for selection, odds in ((home, home_odds), (away, away_odds)):
            if odds is None or odds <= 1.0:
                continue
            rows.append({
                "event_id": ev["id"],
                "event_date": event_date,
                "sport": sport,
                "home_team": home,
                "away_team": away,
                "market": "moneyline",
                "selection": selection,
                "odds_decimal": float(odds),
                "closing_odds_decimal": float(odds),  # same until event closes
                "result": None,  # unknown until event settles
            })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("event_date").reset_index(drop=True)
    return df


def fetch_all_sports_df(api_key: str, sports: List[str], regions: str = "eu") -> pd.DataFrame:
    """Fetch and merge odds for every sport in the list."""
    frames = []
    for sport in sports:
        try:
            events = fetch_upcoming_odds(api_key, sport, regions)
            df = odds_to_dataframe(events, sport)
            if not df.empty:
                frames.append(df)
        except requests.HTTPError as exc:
            log.error("Failed to fetch sport '%s': %s", sport, exc)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
