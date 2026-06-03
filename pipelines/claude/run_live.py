"""
Run the live betting pipeline.

Usage:
    # Dry-run (no real bets, just logs what would be placed):
    python pipelines/claude/run_live.py

    # Actually place bets on Betplay (make sure .env is configured):
    python pipelines/claude/run_live.py --live

Prerequisites:
    1. Copy .env.example to .env and fill in ODDS_API_KEY, BETPLAY_EMAIL, BETPLAY_PASSWORD.
    2. pip install -r requirements.txt
    3. python -m playwright install chromium
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.pipeline_live import run


def main():
    parser = argparse.ArgumentParser(description="Betplay live betting pipeline")
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Place real bets. Omit this flag for a safe dry-run that only logs.",
    )
    args = parser.parse_args()

    dry_run = not args.live
    if not dry_run:
        print("\n*** WARNING: --live flag is set. Real bets will be placed on Betplay. ***")
        confirm = input("Type YES to continue, anything else to abort: ").strip()
        if confirm != "YES":
            print("Aborted.")
            sys.exit(0)

    result = run(dry_run=dry_run)
    print("\nRun summary:")
    for k, v in result.items():
        if k != "bets":
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
