"""Print the full last_bets.json response so we can read bet_rows structure."""
import json, os
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

BASE   = os.getenv("STAKE_API_BASE")
TOKEN  = os.getenv("STAKE_TOKEN")
PLAYER = os.getenv("STAKE_PLAYER_ID")
FRAN   = os.getenv("STAKE_FRANCHISE", "115")

PARAMS = {"token": TOKEN, "franchise": FRAN, "countryCode": "co", "player_id": PLAYER}
HEADERS = {
    "accept": "application/json",
    "origin": "https://stake.com.co",
    "referer": "https://stake.com.co/",
    "user-agent": "Mozilla/5.0 Chrome/148.0.0.0",
}

r = requests.get(BASE.rstrip("/") + "/last_bets.json", params=PARAMS, headers=HEADERS, timeout=10)
data = r.json()
bets = data.get("last_bets", {})
for bet_id, bet in bets.items():
    print(f"\n=== Bet {bet_id} ===")
    print(json.dumps(bet, indent=2, ensure_ascii=False))
