import json
from pathlib import Path
from typing import Any, Dict
import pandas as pd


def save_metrics(metrics: Dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)


def save_ledger(ledger: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(output_dir / "ledger.csv", index=False)
