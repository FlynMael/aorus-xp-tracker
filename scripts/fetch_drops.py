import csv
import os
from datetime import datetime, timezone

import requests

DROPS_API = "https://aorus-drops-analytics.vercel.app/api/drops"
FIELDNAMES = ["date", "horario", "nick", "classe", "item", "monster", "mapa"]

# Cada grupo tem sua propria lista de players e seu proprio arquivo de drops,
# totalmente separados um do outro.
GROUPS = [
    {"players_file": "players.txt", "data_file": "data/drops.csv"},
    {"players_file": "players_grupo2.txt", "data_file": "data/drops_grupo2.csv"},
]


def load_players(players_file):
    with open(players_file, encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip()}


def load_existing_keys(data_file):
    seen = set()
    if os.path.exists(data_file):
        with open(data_file, newline="", encoding="utf-8") as f:
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


def process_group(group, date_str, drops):
    players = load_players(group["players_file"])
    data_file = group["data_file"]
    existing = load_existing_keys(data_file)

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
        print(f"[{data_file}] Nenhum drop novo.")
        return

    os.makedirs(os.path.dirname(data_file), exist_ok=True)
    file_exists = os.path.exists(data_file)

    with open(data_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_rows)

    print(f"[{data_file}] {len(new_rows)} novo(s) drop(s) adicionado(s).")


def main():
    date_str, drops = fetch_today_drops()
    for group in GROUPS:
        process_group(group, date_str, drops)


if __name__ == "__main__":
    main()
