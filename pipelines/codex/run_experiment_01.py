"""Run Experiment 01 — Baseline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pipelines.codex.src.pipeline_01 import run

if __name__ == "__main__":
    run()
