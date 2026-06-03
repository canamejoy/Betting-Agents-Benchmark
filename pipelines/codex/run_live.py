"""Run the live betting pipeline.

  python pipelines/codex/run_live.py          # dry-run
  python pipelines/codex/run_live.py --live   # real bets
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pipelines.codex.src.pipeline_live import run

if __name__ == "__main__":
    live = "--live" in sys.argv
    run(live=live)
