"""
Regression tests for the 3 bugs found in broken_pipeline/pipeline.py.

Each test demonstrates the incorrect behaviour of the buggy code and
verifies that the fixed code in pipeline_03.py produces the right result.
"""
import pandas as pd
import pytest

from src.pipeline_03 import compute_implied_probability, simulate_backtest, compute_metrics


# ---------------------------------------------------------------------------
# BUG 1 — Implied probability formula
# ---------------------------------------------------------------------------

class TestImpliedProbabilityBug:
    """Bug: used odds/(1+odds) instead of 1/odds."""

    @pytest.mark.parametrize("odds, expected", [
        (2.00, 0.500),
        (1.50, 0.6667),
        (3.00, 0.3333),
        (4.00, 0.250),
        (1.20, 0.8333),
    ])
    def test_correct_formula(self, odds, expected):
        result = compute_implied_probability(odds)
        assert abs(result - expected) < 1e-3, (
            f"odds={odds}: got {result:.6f}, expected {expected:.4f}"
        )

    def test_wrong_formula_would_fail(self):
        buggy = lambda o: o / (1 + o)
        fixed = compute_implied_probability
        for odds in [1.5, 2.0, 3.0]:
            assert buggy(odds) != fixed(odds), (
                f"Bug and fix produced same value for odds={odds}"
            )

    def test_implied_prob_always_between_0_and_1(self):
        for odds in [1.01, 1.5, 2.0, 5.0, 10.0]:
            p = compute_implied_probability(odds)
            assert 0 < p <= 1.0


# ---------------------------------------------------------------------------
# BUG 2 — Push treated as loss
# ---------------------------------------------------------------------------

class TestPushSettlementBug:
    """Bug: else branch applied -stake to both 'loss' and 'push'."""

    def _single_bet(self, result, odds=2.0, stake=1.0):
        bets = pd.DataFrame([{
            "event_id": 1,
            "result": result,
            "odds_decimal": odds,
            "model_prob": 0.60,
            "ev": 0.20,
        }])
        results_df, _ = simulate_backtest(bets, stake)
        return results_df.iloc[0]["pnl"]

    def test_push_pnl_is_zero(self):
        pnl = self._single_bet("push")
        assert pnl == 0.0, f"Push must return 0 pnl, got {pnl}"

    def test_loss_pnl_is_negative_stake(self):
        pnl = self._single_bet("loss", stake=1.0)
        assert pnl == -1.0

    def test_win_pnl_is_positive(self):
        pnl = self._single_bet("win", odds=2.0, stake=1.0)
        assert abs(pnl - 1.0) < 1e-9

    def test_push_does_not_reduce_bankroll(self):
        bets = pd.DataFrame([
            {"event_id": 0, "result": "win",  "odds_decimal": 2.0, "model_prob": 0.6, "ev": 0.2},
            {"event_id": 1, "result": "push", "odds_decimal": 2.0, "model_prob": 0.6, "ev": 0.2},
        ])
        results_df, _ = simulate_backtest(bets, stake=1.0)
        bankrolls = results_df["bankroll"].tolist()
        # After win: bankroll relative to initial + 1.0; after push: unchanged
        assert bankrolls[0] > 1000.0  # won
        assert bankrolls[1] == bankrolls[0]  # push left it unchanged


# ---------------------------------------------------------------------------
# BUG 3 — ROI divided by bet count instead of total staked
# ---------------------------------------------------------------------------

class TestROIBug:
    """Bug: roi = total_profit / len(results_df) instead of / total_stake."""

    def _results_df(self, pnls, stake=1.0):
        records = []
        bankroll = 1000.0
        for i, pnl in enumerate(pnls):
            result = "win" if pnl > 0 else ("push" if pnl == 0 else "loss")
            bankroll += pnl
            records.append({"event_id": i, "result": result,
                            "stake": stake, "pnl": pnl, "bankroll": bankroll})
        return pd.DataFrame(records)

    def test_roi_is_profit_over_total_staked(self):
        # 2 wins at odds 2.0 (pnl=+1 each), stake=1 each → total_profit=2, total_stake=2, ROI=1.0
        df = self._results_df([1.0, 1.0], stake=1.0)
        metrics = compute_metrics(df, max_drawdown=0.0, runtime=0.0)
        assert abs(metrics["roi"] - 1.0) < 1e-9

    def test_roi_differs_from_buggy_formula(self):
        # stake=5, 3 bets: profit=5, total_stake=15, correct ROI≈0.3333
        # buggy formula gave: 5/3=1.667
        df = self._results_df([5.0, -5.0, 5.0], stake=5.0)
        metrics = compute_metrics(df, max_drawdown=0.0, runtime=0.0)
        expected_roi = 5.0 / 15.0  # ≈ 0.3333
        assert abs(metrics["roi"] - expected_roi) < 1e-4, (
            f"Expected ROI≈{expected_roi:.4f}, got {metrics['roi']}"
        )

    def test_roi_zero_bets(self):
        df = pd.DataFrame(columns=["event_id", "result", "stake", "pnl", "bankroll"])
        metrics = compute_metrics(df, max_drawdown=0.0, runtime=0.0)
        assert metrics["roi"] == 0.0

    def test_roi_key_exists_in_metrics(self):
        df = self._results_df([1.0])
        metrics = compute_metrics(df, max_drawdown=0.0, runtime=0.0)
        assert "roi" in metrics
        assert "total_profit" in metrics
        assert "hit_rate" in metrics
