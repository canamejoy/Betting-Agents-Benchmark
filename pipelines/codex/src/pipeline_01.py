"""Experiment 01 — Baseline model: flat staking."""

import time
from pathlib import Path

from .config import EXPERIMENT_01
from .data import load_data, chronological_split
from .features import FeaturePipeline
from .model import BettingModel
from .betting import select_bets
from .backtest import run_flat
from .metrics_calc import compute_betting_metrics
from .reporting import save_metrics, save_results, print_summary

RUNS_DIR = Path(__file__).resolve().parents[1] / "runs" / "experiment_01"


def run(cfg: dict = None) -> dict:
    cfg = cfg or EXPERIMENT_01
    t0 = time.time()

    df = load_data(cfg["data_path"])
    train_df, eval_df = chronological_split(df, cfg["train_ratio"])

    fp = FeaturePipeline()
    train_df = fp.fit_transform(train_df)
    eval_df = fp.transform(eval_df)

    model = BettingModel(random_state=cfg["random_state"])
    model.fit(train_df)

    probs = model.predict_proba(eval_df)
    bets = select_bets(eval_df, probs, cfg["ev_threshold"])

    results_df, max_drawdown = run_flat(bets, cfg["flat_stake"], cfg["initial_bankroll"])
    runtime = time.time() - t0

    metrics = compute_betting_metrics(results_df, runtime)
    metrics["max_drawdown"] = round(float(max_drawdown), 4)

    print_summary(metrics)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    save_metrics(metrics, RUNS_DIR / "metrics.json")
    save_results(results_df, RUNS_DIR / "results.csv")

    return metrics


if __name__ == "__main__":
    run()
