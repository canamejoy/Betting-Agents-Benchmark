"""Run experiment 02 from the repo root: python pipelines/claude/run_experiment_02.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.pipeline_02 import run

if __name__ == "__main__":
    run()
