import csv
import os
from datetime import datetime, timedelta, timezone

import requests

API_URL = "https://aorus-xp-tracker.vercel.app/api/data"
FIELDNAMES = ["created_at", "name", "clan", "level", "percent", "battleEXP", "kills", "classId"]

# Cada grupo tem sua propria lista de players e seu proprio arquivo de dados,
# totalmente separados um do outro.
GROUPS = [
    {"players_file": "players.txt", "data_file": "data/history.csv"},
    {"players_file": "players_grupo2.txt", "data_file": "data/history_grupo2.csv"},
]


def load_players(players_file):
    with open(players_file, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def load_existing_keys(data_file):
    seen = set()
    if os.path.exists(data_file):
        with open(data_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                seen.add((row["created_at"], row["name"]))
    return seen


def fetch_snapshots():
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=26)  # margem de seguranca contra execucoes perdidas
    params = {
        "start": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "end": end.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    }
    resp = requests.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def process_group(group, snapshots):
    players = load_players(group["players_file"])
    data_file = group["data_file"]
    existing = load_existing_keys(data_file)

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
        print(f"[{data_file}] Nenhum dado novo.")
        return

    os.makedirs(os.path.dirname(data_file), exist_ok=True)
    file_exists = os.path.exists(data_file)
    new_rows.sort(key=lambda r: (r["created_at"], r["name"]))

    with open(data_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_rows)

    print(f"[{data_file}] {len(new_rows)} novos registros adicionados.")


def main():
    snapshots = fetch_snapshots()
    for group in GROUPS:
        process_group(group, snapshots)


if __name__ == "__main__":
    main()
