"""Fetch live odds from The Odds API."""

import requests


ODDS_API_BASE = "https://api.the-odds-api.com/v4"

SPORT_MAP = {
    "soccer_epl": "soccer",
    "basketball_nba": "basketball",
    "tennis_atp_french_open": "tennis",
}


def fetch_sports(api_key: str) -> list:
    url = f"{ODDS_API_BASE}/sports"
    resp = requests.get(url, params={"apiKey": api_key}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_odds(api_key: str, sport_key: str, regions: str = "eu", markets: str = "h2h") -> list:
    url = f"{ODDS_API_BASE}/sports/{sport_key}/odds"
    params = {
        "apiKey": api_key,
        "regions": regions,
        "markets": markets,
        "oddsFormat": "decimal",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def parse_odds_response(games: list, sport_label: str) -> list:
    """Convert Odds API response to benchmark schema rows."""
    rows = []
    for game in games:
        home = game.get("home_team", "")
        away = game.get("away_team", "")
        event_date = game.get("commence_time", "")[:10]
        event_id = game.get("id", "")
        for bookmaker in game.get("bookmakers", [])[:1]:  # first bookmaker only
            for market in bookmaker.get("markets", []):
                if market["key"] != "h2h":
                    continue
                for outcome in market.get("outcomes", []):
                    rows.append({
                        "event_id": event_id,
                        "event_date": event_date,
                        "sport": sport_label,
                        "home_team": home,
                        "away_team": away,
                        "market": "moneyline",
                        "selection": outcome["name"],
                        "odds_decimal": outcome["price"],
                        "closing_odds_decimal": None,
                        "result": None,
                    })
    return rows
