import csv
import os
from datetime import datetime, timedelta, timezone

import requests

API_URL = "https://aorus-xp-tracker.vercel.app/api/data"
DATA_FILE = "data/history.csv"
PLAYERS_FILE = "players.txt"
FIELDNAMES = ["created_at", "name", "clan", "level", "percent", "battleEXP", "kills", "classId"]


def load_players():
    with open(PLAYERS_FILE, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def load_existing_keys():
    seen = set()
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                seen.add((row["created_at"], row["name"]))
    return seen


def fetch_snapshots():
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=26)  # margem de segurança contra execuções perdidas
    params = {
        "start": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "end": end.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    }
    resp = requests.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main():
    players = load_players()
    existing = load_existing_keys()
    snapshots = fetch_snapshots()

    new_rows = []
    for snap in snapshots:
        created_at = snap.get("created_at")
        for p in snap.get("data", []):
            key = (created_at, p.get("name"))
            if p.get("name") in players and key not in existing:
                new_rows.append({
                    "created_at": created_at,
                    "name": p.get("name"),
                    "clan": p.get("clan"),
                    "level": p.get("level"),
                    "percent": p.get("percent"),
                    "battleEXP": p.get("battleEXP"),
                    "kills": p.get("kills"),
                    "classId": p.get("classId"),
                })

    if not new_rows:
        print("Nenhum dado novo.")
        return

    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    file_exists = os.path.exists(DATA_FILE)
    new_rows.sort(key=lambda r: (r["created_at"], r["name"]))

    with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_rows)

    print(f"{len(new_rows)} novos registros adicionados.")


if __name__ == "__main__":
    main()
