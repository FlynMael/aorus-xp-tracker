import csv
import os
from datetime import datetime, timezone

import requests

DROPS_API = "https://aorus-drops-analytics.vercel.app/api/drops"
DATA_FILE = "data/drops.csv"
PLAYERS_FILE = "players.txt"
FIELDNAMES = ["date", "horario", "nick", "classe", "item", "monster", "mapa"]


def load_players():
    with open(PLAYERS_FILE, encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip()}


def load_existing_keys():
    seen = set()
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = (row["date"], row["nick"], row["item"], row["horario"], row["monster"], row["mapa"])
                seen.add(key)
    return seen


def fetch_today_drops():
    now = datetime.now(timezone.utc)
    params = {"day": now.day, "month": now.month, "year": now.year, "t": int(now.timestamp() * 1000)}
    resp = requests.get(DROPS_API, params=params, timeout=30)
    resp.raise_for_status()
    return now.strftime("%Y-%m-%d"), resp.json()


def main():
    players = load_players()
    existing = load_existing_keys()
    date_str, drops = fetch_today_drops()

    new_rows = []
    for d in drops:
        nick = d.get("nick", "")
        if nick.lower() not in players:
            continue
        item = d.get("item", "")
        horario = d.get("horario", "")
        monster = d.get("monster", "")
        mapa = d.get("mapa", "")
        key = (date_str, nick, item, horario, monster, mapa)
        if key in existing:
            continue
        new_rows.append({
            "date": date_str,
            "horario": horario,
            "nick": nick,
            "classe": d.get("classe", ""),
            "item": item,
            "monster": monster,
            "mapa": mapa,
        })
        existing.add(key)

    if not new_rows:
        print("Nenhum drop novo.")
        return

    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    file_exists = os.path.exists(DATA_FILE)

    with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_rows)

    print(f"{len(new_rows)} novo(s) drop(s) adicionado(s).")


if __name__ == "__main__":
    main()
