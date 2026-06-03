"""Experiment 01 — Baseline Model: logistic regression + flat staking."""
import logging
import time

from .config import EXPERIMENT_01 as CFG
from .data import load_data, chronological_split
from .features import FeatureEncoder
from .model import train_model, predict_win_prob
from .betting import add_ev, select_bets
from .backtest import simulate_flat
from .metrics_calc import betting_metrics
from .reporting import save_metrics, save_ledger

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def run():
    t0 = time.time()
    log.info("=== Experiment 01: Baseline Model ===")

    df = load_data(CFG["data_path"])
    log.info("Loaded %d rows from %s", len(df), CFG["data_path"])

    train_df, test_df = chronological_split(df, CFG["train_ratio"])
    log.info("Split: train=%d  test=%d  (ratio=%.0f%%)", len(train_df), len(test_df), CFG["train_ratio"] * 100)

    encoder = FeatureEncoder()
    train_feats = encoder.fit_transform(train_df)
    test_feats = encoder.transform(test_df)

    clf = train_model(train_feats)
    log.info("Logistic regression trained")

    test_feats = test_feats.copy()
    test_feats["model_prob"] = predict_win_prob(clf, test_feats)
    test_feats = add_ev(test_feats)
    bets = select_bets(test_feats, CFG["ev_threshold"])
    log.info("Bets selected: %d / %d  (EV > %.2f)", len(bets), len(test_df), CFG["ev_threshold"])

    sim = simulate_flat(bets, CFG["flat_stake"])
    runtime = time.time() - t0

    metrics = betting_metrics(sim, runtime)
    log.info("Results: profit=%.4f  ROI=%.2f%%  hit_rate=%.2f%%  bets=%d  drawdown=%.4f",
             metrics["total_profit"], metrics["roi"] * 100, metrics["hit_rate"] * 100,
             metrics["bet_count"], metrics["max_drawdown"])

    save_metrics(metrics, CFG["output_dir"])
    save_ledger(sim["ledger"], CFG["output_dir"])
    log.info("Saved to %s", CFG["output_dir"])
    return metrics


if __name__ == "__main__":
    run()
