"""Experiment 02 — Risk-Aware Bankroll: fractional Kelly + stake/exposure caps."""
import logging
import time

from .config import EXPERIMENT_02 as CFG
from .data import load_data, chronological_split
from .features import FeatureEncoder
from .model import train_model, predict_win_prob
from .betting import add_ev, select_bets
from .backtest import simulate_kelly
from .metrics_calc import risk_metrics
from .reporting import save_metrics, save_ledger

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def run():
    t0 = time.time()
    log.info("=== Experiment 02: Risk-Aware Bankroll ===")

    df = load_data(CFG["data_path"])
    train_df, test_df = chronological_split(df, CFG["train_ratio"])
    log.info("Split: train=%d  test=%d", len(train_df), len(test_df))

    encoder = FeatureEncoder()
    train_feats = encoder.fit_transform(train_df)
    test_feats = encoder.transform(test_df)

    clf = train_model(train_feats)
    test_feats = test_feats.copy()
    test_feats["model_prob"] = predict_win_prob(clf, test_feats)
    test_feats = add_ev(test_feats)
    bets = select_bets(test_feats, CFG["ev_threshold"])
    log.info("Bets selected: %d  (EV > %.2f)", len(bets), CFG["ev_threshold"])

    sim = simulate_kelly(
        bets,
        initial_bankroll=CFG["initial_bankroll"],
        kelly_fraction=CFG["kelly_fraction"],
        max_stake_pct=CFG["max_stake_pct"],
        max_daily_exposure_pct=CFG["max_daily_exposure_pct"],
    )
    runtime = time.time() - t0

    metrics = risk_metrics(sim, runtime)
    log.info("Results: profit=%.4f  ROI=%.2f%%  max_drawdown=%.4f  sharpe=%.4f  final_bankroll=%.2f",
             metrics["total_profit"], metrics["roi"] * 100, metrics["max_drawdown"],
             metrics["sharpe_like_ratio"], metrics["final_bankroll"])

    save_metrics(metrics, CFG["output_dir"])
    save_ledger(sim["ledger"], CFG["output_dir"])
    log.info("Saved to %s", CFG["output_dir"])
    return metrics


if __name__ == "__main__":
    run()
