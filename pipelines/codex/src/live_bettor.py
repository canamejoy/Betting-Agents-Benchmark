"""Place bets on stake.com.co via its sportsbook API (websbkt.com backend).

Architecture (discovered from network analysis):
  - Sports data + bet history: https://auth-115o-sp.websbkt.com/115/es/America-Bogota/
      GET  /last_bets.json        — player bet history (confirmed working)
  - Bet placement: fe-api.stake.com.co REST API
      POST /restapi/v1/<endpoint>?cfid=<event_id>  — to be confirmed

Authentication:
  Two separate auth systems:
    1. websbkt.com: token + player_id query params (for bet history)
    2. fe-api.stake.com.co: session_id cookie (for bet placement)

Bet structure (from last_bets.json):
  odd_id    — outcome ID (3 = away/visitor win in this league)
  event_id  — event identifier
  odd_value — decimal odds
  amount    — stake in COP
  bet_type  — 1 = single
"""

import json
import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_WEBSBKT_BASE = "https://auth-115o-sp.websbkt.com/115/es/America-Bogota"
_FE_BASE      = "https://fe-api.stake.com.co/restapi/v1"


class StakeBettor:
    def __init__(
        self,
        email: str,
        password: str,
        dry_run: bool = True,
        session_id: str = "",
        api_base: str = "",
        token: str = "",
        player_id: str = "",
        franchise: str = "115",
    ):
        self.email = email
        self.password = password
        self.dry_run = dry_run
        self._session_id = session_id or os.getenv("STAKE_SESSION_ID", "")
        self._token      = token      or os.getenv("STAKE_TOKEN", "")
        self._player_id  = player_id  or os.getenv("STAKE_PLAYER_ID", "")
        self._franchise  = franchise  or os.getenv("STAKE_FRANCHISE", "115")
        self._fe_http    = requests.Session()
        self._wb_http    = requests.Session()

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self):
        if not self.dry_run:
            missing = [k for k, v in [
                ("STAKE_SESSION_ID", self._session_id),
                ("STAKE_TOKEN",      self._token),
                ("STAKE_PLAYER_ID",  self._player_id),
            ] if not v]
            if missing:
                raise RuntimeError(f"Missing credentials: {', '.join(missing)}")

            self._fe_http.headers.update(self._fe_headers())
            self._wb_http.headers.update(self._wb_headers())
            logger.info("StakeBettor ready (live mode)")
        else:
            logger.info("StakeBettor ready (dry-run mode)")
        return self

    def __exit__(self, *_):
        self._fe_http.close()
        self._wb_http.close()
        return False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def place_bet(
        self,
        selection: str,
        odds_decimal: float,
        stake_usd: float,
        home_team: str = "",
        away_team: str = "",
        **_,
    ) -> dict:
        if self.dry_run:
            logger.info("[DRY RUN] Would bet $%.4f on '%s' @ %.2f", stake_usd, selection, odds_decimal)
            return {"selection": selection, "odds_decimal": odds_decimal, "stake_usd": stake_usd, "status": "dry_run"}

        # Match against the user's recent bets to get odd_id + event_id
        event = self._find_event_from_history(home_team or selection, away_team, odds_decimal)
        if not event:
            logger.warning("No recent event found for '%s' vs '%s' @ %.2f", home_team, away_team, odds_decimal)
            return {"selection": selection, "status": "event_not_found"}

        stake_cop = round(stake_usd / float(os.getenv("COP_TO_USD_RATE", "0.00025")))
        return self._submit_bet(selection, event, stake_cop, odds_decimal)

    def fetch_last_bets(self) -> list:
        """Return the player's recent bet history from websbkt.com."""
        r = self._wb_http.get(
            _WEBSBKT_BASE + "/last_bets.json",
            params=self._wb_params(),
            timeout=10,
        )
        if r.status_code != 200:
            logger.error("last_bets.json => %s %s", r.status_code, r.text[:200])
            return []
        data = r.json()
        bets = data.get("last_bets", {})
        return list(bets.values())

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_event_from_history(
        self, home_or_selection: str, away: str, target_odds: float
    ) -> Optional[dict]:
        """Find an event in the recent bet history matching teams + odds."""
        bets = self.fetch_last_bets()
        query = home_or_selection.lower()
        for bet in bets:
            t1 = (bet.get("team_name_1") or "").lower()
            t2 = (bet.get("team_name_2") or "").lower()
            choice = (bet.get("choice") or "").lower()
            if query in (t1, t2, choice):
                for row in bet.get("bet_rows", []):
                    if abs(row.get("odd_value", 0) - target_odds) < 0.20:
                        return {
                            "odd_id":   row["odd_id"],
                            "event_id": row["event_id"],
                            "odd_value": row["odd_value"],
                        }
        return None

    def _submit_bet(
        self,
        selection: str,
        event: dict,
        stake_cop: int,
        odds_decimal: float,
    ) -> dict:
        """
        POST the bet to fe-api.stake.com.co.
        Endpoint TBD — update _BET_PATH once user confirms the confirm-bet request URL.
        """
        _BET_PATH = "/bet_slips"   # ← update once confirmed from DevTools
        payload = {
            "odd_id":    event["odd_id"],
            "event_id":  event["event_id"],
            "odd_value": event["odd_value"],
            "amount":    stake_cop,
            "bet_type":  1,
        }
        url = _FE_BASE + _BET_PATH
        logger.info("POST %s  body=%s", url, json.dumps(payload))
        try:
            r = self._fe_http.post(url, json=payload, timeout=10)
        except Exception as exc:
            logger.error("Bet POST failed: %s", exc)
            return {"selection": selection, "status": "network_error", "error": str(exc)}

        logger.info("Bet response %s: %s", r.status_code, r.text[:300])
        if r.status_code in (200, 201):
            try:
                body = r.json()
            except Exception:
                body = {"raw": r.text}
            return {
                "selection":    selection,
                "odds_decimal": odds_decimal,
                "stake_cop":    stake_cop,
                "status":       body.get("status") or body.get("Success") or "submitted",
                "response":     body,
            }
        return {
            "selection": selection,
            "status":    f"http_{r.status_code}",
            "body":      r.text[:300],
        }

    def _fe_headers(self) -> dict:
        return {
            "session_id":   self._session_id,
            "cookie":       f"session_id={self._session_id}",
            "content-type": "application/json",
            "content-language": "es",
            "origin":       "https://stake.com.co",
            "referer":      "https://stake.com.co/",
            "user-agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/148.0.0.0 Safari/537.36",
        }

    def _wb_headers(self) -> dict:
        return {
            "accept":       "application/json",
            "origin":       "https://stake.com.co",
            "referer":      "https://stake.com.co/",
            "user-agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/148.0.0.0 Safari/537.36",
        }

    def _wb_params(self) -> dict:
        return {
            "token":       self._token,
            "franchise":   self._franchise,
            "countryCode": "co",
            "player_id":   self._player_id,
        }
