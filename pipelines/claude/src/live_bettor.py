"""
Playwright-based automation for stake.com (Spanish / es-CO locale).

Flow:
  1. Go to stake.com and sign in via the modal.
  2. For each selected bet: navigate to the sport, find the event,
     click the odds, fill stake in USD, confirm.
  3. In dry-run mode: log what would be placed without clicking Apostar.

Currency note:
  The pipeline works internally in COP. Stake.com uses USD.
  Conversion uses the cop_to_usd_rate from config (~4000 COP = $1 USD).
  10 000 COP ≈ $2.50 USD → max stake per bet ≈ $0.12 USD.

IMPORTANT: Stake may update their HTML at any time.
If a selector stops working, open stake.com in a browser, inspect the element,
and update the SELECTORS dict below. All adjustable selectors live there.
Spanish text variants are prioritised; English fallbacks are comma-separated.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd
from playwright.sync_api import Page, Playwright, sync_playwright, TimeoutError as PWTimeout

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Adjustable selectors — Spanish first, English fallback after comma.
# Update these if Stake changes their markup.
# ---------------------------------------------------------------------------
SELECTORS = {
    # Header auth — Stake shows "Iniciar sesión" in Spanish locale
    "sign_in_btn": (
        "button:has-text('Iniciar sesión'), "
        "a:has-text('Iniciar sesión'), "
        "button:has-text('Sign In'), "
        "a:has-text('Sign In')"
    ),
    "email_input": (
        "input[name='email'], "
        "input[type='email'], "
        "input[placeholder*='Correo' i], "
        "input[placeholder*='email' i]"
    ),
    "password_input": (
        "input[name='password'], "
        "input[type='password'], "
        "input[placeholder*='Contraseña' i], "
        "input[placeholder*='password' i]"
    ),
    # Submit inside the login modal — avoid clicking the header Sign In again
    "submit_login": (
        "button[type='submit']:has-text('Iniciar sesión'), "
        "button[type='submit']:has-text('Sign In'), "
        "button[data-cy='login-submit'], "
        "form button[type='submit']"
    ),
    # Balance shows after login
    "balance_indicator": (
        "[data-cy='header-balance'], "
        "[class*='balance' i], "
        "[class*='Balance']"
    ),
    # Sports navigation link
    "sports_nav": (
        "a[href*='/es/sports'], "
        "a[href*='/sports'], "
        "a:has-text('Deportes'), "
        "a:has-text('Sports')"
    ),
    # Search box inside the sports section
    "search_input": (
        "input[placeholder*='Buscar' i], "
        "input[placeholder*='Search' i], "
        "input[type='search']"
    ),
    # Generic event / match row containers
    "event_row": (
        "[data-cy*='event'], "
        "[class*='event' i], "
        "[class*='match' i], "
        "[class*='fixture' i]"
    ),
    # Odds buttons (decimal value as visible text)
    "odds_button": (
        "[data-cy*='odd'], "
        "[class*='odd' i], "
        "[class*='outcome' i], "
        "[class*='Odd']"
    ),
    # Bet slip stake input — Stake uses a numeric amount field
    "bet_slip_stake": (
        "input[data-cy='stake-input'], "
        "input[placeholder*='0.00'], "
        "input[placeholder*='Importe' i], "
        "input[placeholder*='Monto' i], "
        "input[placeholder*='Stake' i], "
        "input[placeholder*='Bet Amount' i]"
    ),
    # Confirm / place bet button
    "place_bet_btn": (
        "button:has-text('Apostar'), "
        "button:has-text('Realizar apuesta'), "
        "button[data-cy='place-bet'], "
        "button:has-text('Place Bet'), "
        "button:has-text('Bet Now')"
    ),
    "bet_slip_close": (
        "button[aria-label*='cerrar' i], "
        "button[aria-label*='close' i], "
        "button[data-cy='close-betslip']"
    ),
}

STAKE_URL = "https://stake.com"

# Odds API sport key → Stake URL path + Spanish/English display label
SPORT_MAP: Dict[str, Dict[str, str]] = {
    "soccer_colombia_primera_a": {"path": "soccer",     "label_es": "Fútbol",      "label_en": "Soccer"},
    "soccer_spain_la_liga":      {"path": "soccer",     "label_es": "Fútbol",      "label_en": "Soccer"},
    "soccer_epl":                {"path": "soccer",     "label_es": "Fútbol",      "label_en": "Soccer"},
    "soccer_england_league1":    {"path": "soccer",     "label_es": "Fútbol",      "label_en": "Soccer"},
    "basketball_nba":            {"path": "basketball", "label_es": "Baloncesto",  "label_en": "Basketball"},
    "tennis_atp_french_open":    {"path": "tennis",     "label_es": "Tenis",       "label_en": "Tennis"},
}


@dataclass
class BetResult:
    event_id: str
    selection: str
    odds: float
    stake_cop: float
    stake_usd: float
    placed: bool
    dry_run: bool
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class StakeSession:
    """Manages a Playwright browser session against stake.com (Spanish locale)."""

    def __init__(
        self,
        email: str,
        password: str,
        dry_run: bool = True,
        headless: bool = False,
        cop_to_usd_rate: float = 0.00025,
    ):
        self.email = email
        self.password = password
        self.dry_run = dry_run
        self.headless = headless
        self.cop_to_usd = cop_to_usd_rate
        self._playwright: Optional[Playwright] = None
        self._page: Optional[Page] = None
        self._results: List[BetResult] = []

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------
    def __enter__(self) -> "StakeSession":
        self._playwright = sync_playwright().start()
        browser = self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=300,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="es-CO",   # Stake serves Spanish when locale is es-CO
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        )
        self._page = ctx.new_page()
        return self

    def __exit__(self, *_):
        if self._page:
            try:
                self._page.close()
            except Exception:
                pass
        if self._playwright:
            self._playwright.stop()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _dismiss_banners(self) -> None:
        """Dismiss cookie / age-check banners if present."""
        for sel in [
            "button:has-text('Aceptar')",
            "button:has-text('Acepto')",
            "button:has-text('Accept')",
            "button:has-text('Tengo 18')",
            "button:has-text('I am 18')",
            "[data-cy='cookie-accept']",
        ]:
            try:
                btn = self._page.locator(sel).first
                if btn.is_visible(timeout=1500):
                    btn.click()
                    log.debug("Dismissed banner: %s", sel)
                    self._page.wait_for_timeout(500)
                    return
            except PWTimeout:
                pass

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    def login(self) -> bool:
        page = self._page
        log.info("Opening stake.com")
        page.goto(STAKE_URL, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(2000)
        self._dismiss_banners()

        # Click Sign In / Iniciar sesión to open the modal.
        try:
            page.locator(SELECTORS["sign_in_btn"]).first.click(timeout=8000)
            page.wait_for_timeout(1200)
        except PWTimeout:
            log.error("Could not find the Sign In / Iniciar sesión button.")
            return False

        # Fill credentials inside the modal.
        try:
            page.locator(SELECTORS["email_input"]).first.fill(self.email, timeout=7000)
            page.locator(SELECTORS["password_input"]).first.fill(self.password)
            page.locator(SELECTORS["submit_login"]).first.click()
            page.wait_for_timeout(3500)
        except PWTimeout as exc:
            log.error("Could not fill login form: %s", exc)
            return False

        # Verify login — wait for balance element.
        try:
            page.locator(SELECTORS["balance_indicator"]).first.wait_for(timeout=14_000)
            log.info("Login successful")
            return True
        except PWTimeout:
            log.error(
                "Login failed — balance not visible after 14 s. "
                "Check credentials, or Stake may require a captcha / 2FA step."
            )
            return False

    # ------------------------------------------------------------------
    # Navigate to sport section
    # ------------------------------------------------------------------
    def navigate_to_sport(self, sport: str) -> None:
        info = SPORT_MAP.get(sport, {"path": "soccer", "label_es": "Fútbol", "label_en": "Soccer"})
        url = f"{STAKE_URL}/es/sports/{info['path']}"
        log.info("Navigating to %s", url)
        self._page.goto(url, wait_until="domcontentloaded", timeout=20_000)
        self._page.wait_for_timeout(1500)

    # ------------------------------------------------------------------
    # Find event and click odds
    # ------------------------------------------------------------------
    def _find_and_click_odds(
        self, home_team: str, away_team: str, selection: str, target_odds: float
    ) -> bool:
        page = self._page

        # Try search box.
        try:
            search = page.locator(SELECTORS["search_input"]).first
            search.fill(home_team, timeout=4000)
            page.wait_for_timeout(1200)
        except PWTimeout:
            log.debug("No search box found — scanning page")

        try:
            from rapidfuzz import fuzz
        except ImportError:
            fuzz = None

        # Direct text match first.
        candidates = page.locator(f"text='{home_team}'").all()

        if not candidates and fuzz:
            containers = page.locator(SELECTORS["event_row"]).all()
            for el in containers:
                try:
                    txt = el.inner_text(timeout=500)
                    if (fuzz.partial_ratio(home_team.lower(), txt.lower()) > 72
                            or fuzz.partial_ratio(away_team.lower(), txt.lower()) > 72):
                        candidates = [el]
                        break
                except Exception:
                    continue

        if not candidates:
            log.warning("Event not found on page: %s vs %s", home_team, away_team)
            return False

        event_el = candidates[0]
        odds_str = f"{target_odds:.2f}"

        # Try exact odds text inside the event element.
        try:
            btn = event_el.locator(f"text='{odds_str}'").first
            btn.click(timeout=5000)
            log.info("Clicked odds %s for %s", odds_str, selection)
            return True
        except PWTimeout:
            pass

        # Tolerance fallback across all odds buttons in the container.
        try:
            all_btns = event_el.locator(SELECTORS["odds_button"]).all()
            for btn in all_btns:
                try:
                    val = float(btn.inner_text(timeout=300).strip())
                    if abs(val - target_odds) < 0.12:
                        btn.click()
                        log.info("Clicked approx odds %.2f (target %.2f)", val, target_odds)
                        return True
                except (ValueError, PWTimeout):
                    continue
        except Exception:
            pass

        log.warning("Could not find odds %.2f for %s", target_odds, selection)
        return False

    # ------------------------------------------------------------------
    # Fill bet slip and confirm
    # ------------------------------------------------------------------
    def _fill_and_confirm_bet_slip(self, stake_cop: float) -> bool:
        page = self._page
        stake_usd = round(max(0.10, stake_cop * self.cop_to_usd), 2)
        stake_str = f"{stake_usd:.2f}"

        if self.dry_run:
            log.info("[DRY-RUN] Would bet: $%s USD  (%.0f COP)", stake_str, stake_cop)
            return True

        try:
            stake_field = page.locator(SELECTORS["bet_slip_stake"]).first
            stake_field.wait_for(timeout=7000)
            stake_field.triple_click()
            stake_field.fill(stake_str)
            page.wait_for_timeout(600)

            place_btn = page.locator(SELECTORS["place_bet_btn"]).first
            place_btn.wait_for(timeout=6000)
            place_btn.click()
            page.wait_for_timeout(2500)
            log.info("Bet placed: $%s USD (%.0f COP)", stake_str, stake_cop)
            return True
        except PWTimeout as exc:
            log.error("Bet slip interaction failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Public: place a single bet
    # ------------------------------------------------------------------
    def place_bet(
        self,
        event_id: str,
        home_team: str,
        away_team: str,
        sport: str,
        selection: str,
        odds: float,
        stake_cop: float,
    ) -> BetResult:
        stake_usd = round(max(0.10, stake_cop * self.cop_to_usd), 2)
        log.info(
            "Bet | %s vs %s | %s | odds=%.2f | %.0f COP ($%.2f) | dry_run=%s",
            home_team, away_team, selection, odds, stake_cop, stake_usd, self.dry_run,
        )

        self.navigate_to_sport(sport)
        clicked = self._find_and_click_odds(home_team, away_team, selection, odds)

        if not clicked:
            result = BetResult(
                event_id=event_id, selection=selection, odds=odds,
                stake_cop=stake_cop, stake_usd=stake_usd,
                placed=False, dry_run=self.dry_run,
                error="Event or odds not found on page",
            )
            self._results.append(result)
            return result

        placed = self._fill_and_confirm_bet_slip(stake_cop)
        result = BetResult(
            event_id=event_id, selection=selection, odds=odds,
            stake_cop=stake_cop, stake_usd=stake_usd,
            placed=placed, dry_run=self.dry_run,
        )
        self._results.append(result)
        return result

    # ------------------------------------------------------------------
    # Place multiple bets from a DataFrame
    # ------------------------------------------------------------------
    def place_bets(
        self, bets_df: pd.DataFrame, bankroll_cop: float, max_stake_pct: float
    ) -> List[BetResult]:
        results = []
        min_cop = (0.10 / self.cop_to_usd)  # minimum COP equivalent of $0.10 USD
        for _, row in bets_df.iterrows():
            stake = float(row.get("stake_cop", bankroll_cop * max_stake_pct))
            stake = max(min_cop, min(stake, bankroll_cop * max_stake_pct))

            res = self.place_bet(
                event_id=str(row["event_id"]),
                home_team=str(row["home_team"]),
                away_team=str(row["away_team"]),
                sport=str(row.get("sport", "soccer_epl")),
                selection=str(row["selection"]),
                odds=float(row["odds_decimal"]),
                stake_cop=stake,
            )
            results.append(res)
            time.sleep(1.5)
        return results

    @property
    def results(self) -> List[BetResult]:
        return list(self._results)
