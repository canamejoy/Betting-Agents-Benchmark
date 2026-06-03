"""Run experiment 03 from the repo root: python pipelines/claude/run_experiment_03.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.pipeline_03 import run

if __name__ == "__main__":
    run()
