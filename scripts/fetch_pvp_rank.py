import json
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

API_URL = "https://aorus-xp-tracker.vercel.app/api/data"
TZ = ZoneInfo("America/Sao_Paulo")
OUT_FILE = "data/pvp_rank.json"
TOP_N = 30


def fetch_snapshots(start, end):
    params = {
        "start": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "end": end.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    }
    resp = requests.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def num(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def player_entry(p):
    return {
        "name": p.get("name"),
        "clan": p.get("clan") or "",
        "level": num(p.get("level")),
        "battleEXP": num(p.get("battleEXP")),
        "kills": num(p.get("kills")),
    }


def main():
    now_utc = datetime.now(timezone.utc)
    now_local = now_utc.astimezone(TZ)
    day_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    start = min(day_start, now_utc - timedelta(hours=3))

    snapshots = [s for s in fetch_snapshots(start, now_utc) if s.get("created_at") and s.get("data")]
    if not snapshots:
        print("Nenhum snapshot retornado pela API.")
        return
    snapshots.sort(key=lambda s: parse_ts(s["created_at"]))

    latest = snapshots[-1]
    latest_players = {p["name"]: player_entry(p) for p in latest["data"] if p.get("name")}

    geral = sorted(latest_players.values(), key=lambda p: (-p["battleEXP"], -p["kills"]))[:TOP_N]

    baseline = {}
    for snap in snapshots:
        if parse_ts(snap["created_at"]) < day_start:
            continue
        for p in snap["data"]:
            name = p.get("name")
            if name and name not in baseline:
                baseline[name] = player_entry(p)

    dia = []
    for name, cur in latest_players.items():
        base = baseline.get(name)
        if not base:
            continue
        kills = cur["kills"] - base["kills"]
        xp = cur["battleEXP"] - base["battleEXP"]
        if kills > 0 or xp > 0:
            dia.append({**cur, "killsDia": kills, "xpDia": xp})

    dia_kills = sorted(dia, key=lambda p: (-p["killsDia"], -p["xpDia"]))[:TOP_N]
    dia_xp = sorted(dia, key=lambda p: (-p["xpDia"], -p["killsDia"]))[:TOP_N]

    out = {
        "updated_at": latest["created_at"],
        "day": now_local.strftime("%Y-%m-%d"),
        "total_players": len(latest_players),
        "geral": geral,
        "dia_kills": dia_kills,
        "dia_xp": dia_xp,
    }

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"[{OUT_FILE}] {len(latest_players)} players no snapshot, {len(dia)} com atividade hoje.")


if __name__ == "__main__":
    main()
