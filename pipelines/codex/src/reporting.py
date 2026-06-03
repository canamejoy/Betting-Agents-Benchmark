"""Export metrics and artifacts."""

import json
from pathlib import Path

import pandas as pd


def save_metrics(metrics: dict, path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved to {path}")


def save_results(results_df: pd.DataFrame, path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(path, index=False)
    print(f"Results saved to {path}")


def print_summary(metrics: dict) -> None:
    print("\n=== Benchmark Summary ===")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    print("=========================\n")
