"""Browser-based betting on stake.com.co using Playwright.

Replaces the fragile direct-API approach in live_bettor.py.
Uses a persistent browser context so login sessions survive between runs.

Setup:
    pip install playwright
    playwright install chromium

Environment variables:
    STAKE_EMAIL            login email
    STAKE_PASSWORD         login password
    STAKE_BASE_URL         default https://stake.com.co
    ODDS_DRIFT_TOLERANCE   max acceptable odds drift, default 0.03 (3%)
    HEADLESS               true/false, default true
    BROWSER_STATE_PATH     session file path, default state/browser_session.json
"""

import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.sync_api import BrowserContext, Page, sync_playwright
from playwright.sync_api import TimeoutError as PWTimeout

logger = logging.getLogger(__name__)

# Odds API sport label -> Stake URL path segment (site uses Spanish slugs)
SPORT_URL_MAP: dict[str, str] = {
    "soccer":            "futbol",
    "basketball":        "baloncesto",
    "tennis":            "tenis",
    "american_football": "futbol-americano",
    "baseball":          "beisbol",
    "hockey":            "hockey",
    "mma":               "mma",
    "boxing":            "boxeo",
}

# Selectors tried in order when dismissing common modals
_POPUP_SELECTORS = [
    "button[aria-label='Close']",
    "button[aria-label='Cerrar']",
    "[class*='modal'] button[class*='close']",
    "[class*='popup'] button[class*='close']",
    "button:has-text('Cerrar')",
    "button:has-text('No, gracias')",
    "button:has-text('Aceptar')",
    "button:has-text('Entendido')",
    "button:has-text('OK')",
]


class BrowserBettor:
    """Place bets on stake.com.co via Playwright browser automation.

    Public interface is identical to StakeBettor so pipeline_live.py
    needs no structural changes beyond swapping the import.
    """

    def __init__(
        self,
        email: str = "",
        password: str = "",
        dry_run: bool = True,
        base_url: str = "",
        odds_drift_tolerance: float = -1.0,
        headless: Optional[bool] = None,
        state_path: str = "",
        # Accept (and ignore) legacy StakeBettor kwargs so callers don't break
        **_legacy_kwargs,
    ):
        self.email    = email    or os.getenv("STAKE_EMAIL", "")
        self.password = password or os.getenv("STAKE_PASSWORD", "")
        self.dry_run  = dry_run

        self.base_url = (
            base_url or os.getenv("STAKE_BASE_URL", "https://stake.com.co")
        ).rstrip("/")

        self.odds_drift_tolerance = (
            odds_drift_tolerance
            if odds_drift_tolerance >= 0
            else float(os.getenv("ODDS_DRIFT_TOLERANCE", "0.03"))
        )

        env_headless = os.getenv("HEADLESS", "true").lower() == "true"
        self.headless = headless if headless is not None else env_headless

        self.state_path = Path(
            state_path or os.getenv("BROWSER_STATE_PATH", "state/browser_session.json")
        )

        self._playwright  = None
        self._browser     = None
        self._context: Optional[BrowserContext] = None
        self._page:    Optional[Page]           = None
        self._screenshots_dir = Path("logs/screenshots")

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self):
        self._screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            # Required for headless Linux servers
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )

        ua = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        ctx_kwargs = dict(viewport={"width": 1280, "height": 900}, user_agent=ua)

        if self.state_path.exists():
            logger.info("Loading browser session from %s", self.state_path)
            ctx_kwargs["storage_state"] = str(self.state_path)
        else:
            logger.info("No saved session — starting fresh browser context")

        self._context = self._browser.new_context(**ctx_kwargs)
        self._page = self._context.new_page()
        self._page.set_default_timeout(15_000)

        if not self.dry_run:
            if not self.email or not self.password:
                raise RuntimeError(
                    "STAKE_EMAIL and STAKE_PASSWORD must be set for live mode"
                )
            self._ensure_logged_in()
            logger.info("BrowserBettor ready (live mode)")
        else:
            logger.info("BrowserBettor ready (dry-run mode)")

        return self

    def __exit__(self, *_):
        if self._context:
            try:
                logger.info("Saving browser session to %s", self.state_path)
                self._context.storage_state(path=str(self.state_path))
            except Exception as exc:
                logger.warning("Could not save session state: %s", exc)
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        return False

    # ------------------------------------------------------------------
    # Public interface  (same signature as StakeBettor.place_bet)
    # ------------------------------------------------------------------

    def place_bet(
        self,
        selection: str,
        odds_decimal: float,
        stake_usd: float,
        home_team: str = "",
        away_team: str = "",
        sport: str = "",
        **_,
    ) -> dict:
        confirm = not self.dry_run

        if self.dry_run:
            logger.info(
                "[DRY RUN] Would bet $%.4f on '%s' @ %.2f",
                stake_usd, selection, odds_decimal,
            )

        try:
            return self._attempt_bet(
                selection, odds_decimal, stake_usd,
                home_team, away_team, sport,
                confirm=confirm,
            )
        except Exception as exc:
            self._screenshot(f"unhandled_{_slug(selection)}")
            logger.error("Unhandled error placing bet on '%s': %s", selection, exc)
            return {
                "selection":    selection,
                "odds_decimal": odds_decimal,
                "stake_usd":    stake_usd,
                "status":       "error",
                "error":        str(exc),
            }

    # ------------------------------------------------------------------
    # Login / session management
    # ------------------------------------------------------------------

    def _ensure_logged_in(self):
        logger.info("Verifying login state …")
        try:
            self._page.goto(
                self.base_url, wait_until="domcontentloaded", timeout=20_000
            )
            self._dismiss_popups()
        except Exception as exc:
            self._screenshot("home_load_error")
            raise RuntimeError(f"Could not load {self.base_url}: {exc}") from exc

        if self._is_logged_in():
            logger.info("Session valid — already logged in")
            return

        logger.info("Not logged in — authenticating …")
        self._login()

    def _is_logged_in(self) -> bool:
        """Return True if a wallet/balance indicator is visible on the page."""
        logged_in_selector = (
            "[data-testid='user-balance'], [class*='userBalance'], "
            "[class*='walletBalance'], [class*='balance__amount'], "
            "[class*='userAvatar'], button[aria-label*='cuenta' i], "
            "button[aria-label*='account' i]"
        )
        try:
            self._page.wait_for_selector(logged_in_selector, timeout=3_000)
            return True
        except PWTimeout:
            return False

    def _login(self):
        """Trigger Stake's auth modal and fill credentials."""
        logger.info("Opening login modal …")

        # Try clicking a login/sign-in trigger
        login_trigger = (
            "button:has-text('Entrar'), button:has-text('Ingresar'), "
            "button:has-text('Sign In'), button:has-text('Log In'), "
            "a:has-text('Entrar'), a:has-text('Ingresar'), "
            "[data-testid*='login'], [data-testid*='sign-in']"
        )
        try:
            self._page.locator(login_trigger).first.click(timeout=5_000)
            time.sleep(0.8)
        except PWTimeout:
            logger.info("Login trigger not found — trying /login URL")
            self._page.goto(
                f"{self.base_url}/login",
                wait_until="domcontentloaded",
                timeout=15_000,
            )

        # Email
        email_sel = (
            "input[type='email'], input[name='email'], "
            "input[placeholder*='email' i], input[placeholder*='correo' i]"
        )
        try:
            email_input = self._page.locator(email_sel).first
            email_input.wait_for(timeout=6_000)
            email_input.fill(self.email)
        except PWTimeout as exc:
            self._screenshot("login_email_missing")
            raise RuntimeError("Email field not found on login form") from exc

        # Password
        try:
            pw_input = self._page.locator("input[type='password']").first
            pw_input.fill(self.password)
        except PWTimeout as exc:
            self._screenshot("login_password_missing")
            raise RuntimeError("Password field not found on login form") from exc

        # Submit
        submit_sel = (
            "button[type='submit'], button:has-text('Entrar'), "
            "button:has-text('Ingresar'), button:has-text('Iniciar sesión'), "
            "button:has-text('Sign In'), [data-testid*='submit']"
        )
        try:
            self._page.locator(submit_sel).first.click(timeout=5_000)
        except PWTimeout as exc:
            self._screenshot("login_submit_missing")
            raise RuntimeError("Login submit button not found") from exc

        time.sleep(3.0)
        self._dismiss_popups()

        if not self._is_logged_in():
            self._screenshot("login_failed")
            raise RuntimeError(
                "Login failed — verify STAKE_EMAIL / STAKE_PASSWORD or handle Cloudflare challenge"
            )

        logger.info("Login successful")

    # ------------------------------------------------------------------
    # Bet placement
    # ------------------------------------------------------------------

    def _attempt_bet(
        self,
        selection: str,
        odds_decimal: float,
        stake_usd: float,
        home_team: str,
        away_team: str,
        sport: str,
        confirm: bool,
    ) -> dict:
        base = {
            "selection":    selection,
            "odds_decimal": odds_decimal,
            "stake_usd":    stake_usd,
        }

        # 1. Navigate to the event
        try:
            self._navigate_to_event(sport, home_team, away_team, selection)
        except Exception as exc:
            self._screenshot(f"nav_fail_{_slug(selection)}")
            return {**base, "status": "navigation_failed", "error": str(exc)}

        # 2. Click the outcome button
        try:
            actual_odds = self._click_outcome(selection, odds_decimal)
        except Exception as exc:
            self._screenshot(f"outcome_fail_{_slug(selection)}")
            return {**base, "status": "outcome_not_found", "error": str(exc)}

        # 3. Check odds drift
        drift = (
            abs(actual_odds - odds_decimal) / odds_decimal
            if odds_decimal > 0 else 0.0
        )
        if drift > self.odds_drift_tolerance:
            logger.warning(
                "Odds drifted %.1f%% for '%s': expected %.2f, got %.2f",
                drift * 100, selection, odds_decimal, actual_odds,
            )
            return {
                **base,
                "status":     "odds_drift_rejected",
                "actual_odds": actual_odds,
                "drift_pct":  round(drift * 100, 2),
            }

        # 4. Fill stake
        try:
            self._fill_stake(stake_usd)
        except Exception as exc:
            self._screenshot(f"stake_fail_{_slug(selection)}")
            return {**base, "status": "stake_fill_failed", "error": str(exc)}

        # 5. Dry-run: stop before confirm
        if not confirm:
            logger.info(
                "[DRY RUN] Stopping before confirm — '%s' @ %.2f", selection, actual_odds
            )
            return {**base, "actual_odds": actual_odds, "status": "dry_run"}

        # 6. Confirm
        try:
            status = self._confirm_bet()
        except Exception as exc:
            self._screenshot(f"confirm_fail_{_slug(selection)}")
            return {**base, "status": "confirm_failed", "error": str(exc)}

        return {**base, "actual_odds": actual_odds, "status": status}

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _navigate_to_event(
        self, sport: str, home_team: str, away_team: str, selection: str
    ):
        sport_slug = SPORT_URL_MAP.get(sport.lower(), sport.lower().replace(" ", "-"))

        # Strategy 1: sport listing page + fuzzy match
        if home_team and away_team:
            sport_url = f"{self.base_url}/sports/{sport_slug}"
            logger.info("Navigating to sport page: %s", sport_url)
            try:
                self._page.goto(
                    sport_url, wait_until="domcontentloaded", timeout=15_000
                )
                self._dismiss_popups()
                if self._find_event_on_page(home_team, away_team):
                    return
                logger.info("Event not found on sport page — trying search")
            except Exception as exc:
                logger.warning("Sport page navigation failed: %s", exc)

        # Strategy 2: search bar
        self._search_for_event(home_team or selection, away_team or "")

    def _find_event_on_page(self, home_team: str, away_team: str) -> bool:
        """Scan current page for a matching event and click it."""
        try:
            from rapidfuzz import fuzz
        except ImportError:
            return False

        event_sel = (
            "[class*='event'], [class*='match'], [class*='game'], "
            "[class*='fixture'], [class*='bout']"
        )
        try:
            elements = self._page.locator(event_sel).all()
        except Exception:
            return False

        for el in elements[:40]:
            try:
                text = el.inner_text(timeout=1_000).lower()
                if (
                    fuzz.partial_ratio(home_team.lower(), text) > 70
                    and fuzz.partial_ratio(away_team.lower(), text) > 70
                ):
                    el.click(timeout=3_000)
                    time.sleep(1.2)
                    return True
            except Exception:
                continue
        return False

    def _search_for_event(self, home_team: str, away_team: str):
        query = f"{home_team} {away_team}".strip()
        logger.info("Searching stake for: %s", query)

        # Open search
        search_trigger = (
            "button[aria-label*='search' i], button[aria-label*='buscar' i], "
            "[data-testid*='search'] button, [class*='searchIcon']"
        )
        try:
            self._page.locator(search_trigger).first.click(timeout=4_000)
            time.sleep(0.4)
        except PWTimeout:
            self._page.goto(self.base_url, wait_until="domcontentloaded", timeout=15_000)
            self._dismiss_popups()

        # Type in search input
        input_sel = (
            "input[type='search'], input[placeholder*='buscar' i], "
            "input[placeholder*='search' i], input[aria-label*='search' i], "
            "input[aria-label*='buscar' i]"
        )
        try:
            inp = self._page.locator(input_sel).first
            inp.wait_for(timeout=5_000)
            inp.fill(query)
            time.sleep(1.8)
        except PWTimeout as exc:
            raise RuntimeError(f"Search input not found: {exc}") from exc

        # Click first result
        result_sel = (
            "[class*='searchResult'], [class*='search-result'], "
            "[class*='suggestion'], [role='option'], "
            "[role='listitem']:has-text('vs'), [role='listitem']:has-text('-')"
        )
        try:
            result = self._page.locator(result_sel).first
            result.wait_for(timeout=4_000)
            result.click()
            time.sleep(1.2)
        except PWTimeout as exc:
            self._screenshot("search_no_results")
            raise RuntimeError(
                f"No search results for '{query}': {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Betslip interactions
    # ------------------------------------------------------------------

    def _click_outcome(self, selection: str, expected_odds: float) -> float:
        """Find the matching outcome button, click it, return actual odds."""
        try:
            from rapidfuzz import fuzz
        except ImportError:
            fuzz = None  # type: ignore[assignment]

        time.sleep(0.5)
        self._dismiss_popups()

        outcome_sel = (
            "button[class*='outcome'], button[class*='odd'], "
            "button[class*='bet'], [class*='outcomeButton'], "
            "[class*='odds-button'], [class*='market'] button, "
            "[class*='selections'] button"
        )

        try:
            candidates = self._page.locator(outcome_sel).all()
        except Exception:
            candidates = []

        best_btn  = None
        best_score = 0
        best_odds  = expected_odds

        for btn in candidates[:60]:
            try:
                text = btn.inner_text(timeout=800).strip()
            except Exception:
                continue
            if not text:
                continue

            score = (
                fuzz.partial_ratio(selection.lower(), text.lower())
                if fuzz else (80 if selection.lower() in text.lower() else 0)
            )

            odds_val = _extract_odds(text)
            if score > best_score and score > 45:
                if odds_val and abs(odds_val - expected_odds) < 0.8:
                    best_btn   = btn
                    best_score = score
                    best_odds  = odds_val
                elif score > 70 and best_btn is None:
                    best_btn   = btn
                    best_score = score

        if best_btn is None:
            # Last-resort: text match on selection name
            try:
                fallback = self._page.locator(
                    f"button:has-text('{selection[:20]}')"
                ).first
                fallback.wait_for(timeout=3_000)
                fallback.click()
                time.sleep(0.8)
                return self._read_betslip_odds() or expected_odds
            except Exception as exc:
                raise RuntimeError(
                    f"Outcome button not found for '{selection}'"
                ) from exc

        logger.info(
            "Clicking '%s' @ %.2f (expected %.2f)", selection, best_odds, expected_odds
        )
        best_btn.click()
        time.sleep(0.8)

        displayed = self._read_betslip_odds()
        return displayed if displayed else best_odds

    def _read_betslip_odds(self) -> Optional[float]:
        """Read odds from the open betslip, or None if not visible."""
        betslip_odds_sel = (
            "[class*='betslip'] [class*='odds'], [class*='betslip'] [class*='odd'], "
            "[class*='slip'] [class*='price'], [data-testid*='betslip'] [class*='odd'], "
            "[class*='betSlip'] [class*='odds']"
        )
        try:
            el = self._page.locator(betslip_odds_sel).first
            el.wait_for(timeout=3_000)
            return _extract_odds(el.inner_text(timeout=800))
        except Exception:
            return None

    def _fill_stake(self, stake_usd: float):
        """Enter the stake amount in the betslip input."""
        stake_input_sel = (
            "[class*='betslip'] input[type='number'], "
            "[class*='betslip'] input[type='text'], "
            "[class*='slip'] input[type='number'], "
            "[class*='betSlip'] input, "
            "[data-testid*='stake-input'], [data-testid*='amount-input']"
        )
        try:
            inp = self._page.locator(stake_input_sel).first
            inp.wait_for(timeout=5_000)
            inp.triple_click()
            inp.fill(f"{stake_usd:.2f}")
            logger.info("Entered stake: $%.4f", stake_usd)
        except PWTimeout as exc:
            raise RuntimeError(f"Stake input not found: {exc}") from exc

    def _confirm_bet(self) -> str:
        """Click the place-bet button and interpret the result."""
        confirm_sel = (
            "button:has-text('Confirmar'), button:has-text('Apostar'), "
            "button:has-text('Realizar apuesta'), button:has-text('Place Bet'), "
            "button:has-text('Confirm Bet'), button:has-text('Place bet'), "
            "[class*='betslip'] button[type='submit'], "
            "[data-testid*='confirm-bet'], [data-testid*='place-bet']"
        )
        try:
            btn = self._page.locator(confirm_sel).first
            btn.wait_for(timeout=5_000)
            btn.click()
            logger.info("Confirm button clicked")
        except PWTimeout as exc:
            raise RuntimeError(f"Confirm button not found: {exc}") from exc

        time.sleep(3.0)
        return self._read_bet_result()

    def _read_bet_result(self) -> str:
        """Infer success/failure from post-confirm page text."""
        content = self._page.content().lower()
        success_kw = [
            "apuesta realizada", "apuesta confirmada", "bet placed",
            "bet confirmed", "felicidades", "congratulations",
        ]
        failure_kw = [
            "error", "falló", "failed", "insuficiente", "insufficient",
            "fondos insuficientes", "insufficient funds",
        ]
        if any(kw in content for kw in success_kw):
            return "placed"
        if any(kw in content for kw in failure_kw):
            return "failed"
        return "submitted"

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _dismiss_popups(self):
        """Silently try to close common modals/popups."""
        for sel in _POPUP_SELECTORS:
            try:
                self._page.locator(sel).first.click(timeout=600)
                time.sleep(0.25)
            except Exception:
                pass

    def _screenshot(self, label: str):
        """Save a debug screenshot — never raises."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self._screenshots_dir / f"{ts}_{label}.png"
        try:
            self._page.screenshot(path=str(path))
            logger.info("Screenshot saved: %s", path)
        except Exception as exc:
            logger.warning("Screenshot failed (%s): %s", label, exc)


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _extract_odds(text: str) -> Optional[float]:
    """Parse the first decimal odds value from a string (e.g. '1.85' or '2\n1.72')."""
    for m in re.findall(r'\b(\d{1,2}\.\d{2,4})\b', text):
        val = float(m)
        if 1.01 <= val <= 100.0:
            return val
    return None


def _slug(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', text.lower())[:30]
