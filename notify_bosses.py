import json
import os
from datetime import datetime, timedelta

import requests
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Bahia")
DEFAULT_NOTIFY_MINUTES = 5
LOG_FILE = "data/boss_notify_log.json"

ONESIGNAL_APP_ID = os.environ.get("ONESIGNAL_APP_ID", "")
ONESIGNAL_REST_API_KEY = os.environ.get("ONESIGNAL_REST_API_KEY", "")

# Mesma lista de bosses/eventos do app (docs/index.html) — se editar um lado, edite o outro.
SCHEDULED_BOSSES = [
    {"nome": "Babel", "local": "Railway of Chaos", "frequencia": "diaria", "horarios": ["02:30", "08:30", "14:30", "18:30"], "notify_minutes": 5},
    {"nome": "Valento", "local": "Gallubia Valey", "frequencia": "diaria", "horarios": ["04:30", "10:30", "16:30", "20:30"], "notify_minutes": 5},
    {"nome": "Kelvezu", "local": "Kelvezu Cave", "frequencia": "diaria", "horarios": ["00:30", "06:30", "12:30", "18:30"], "notify_minutes": 5},
    {"nome": "Mokova", "local": "Lost Temple", "frequencia": "diaria", "horarios": ["02:30", "10:30", "14:30", "20:30"], "notify_minutes": 5},
    {"nome": "Fury", "local": "Endless Tower 1°", "frequencia": "diaria", "horarios": ["04:30", "08:30", "16:30", "22:30"], "notify_minutes": 5},
    {"nome": "Shy", "local": "Endless Tower 3°", "frequencia": "diaria", "horarios": ["00:30", "06:30", "12:30", "22:30"], "notify_minutes": 5},
    {"nome": "Tulla", "local": "Ice Mine", "frequencia": "diaria", "horarios": ["09:00", "15:00", "22:00"], "notify_minutes": 5},
    {"nome": "Aorus God", "local": "Pyramid", "frequencia": "fim_de_semana", "horarios_sabado": ["13:00", "20:30"], "horarios_domingo": ["09:30", "19:30"], "notify_minutes": 5},
    {"nome": "Antrallos", "local": "Expedição", "frequencia": "terca_quinta", "horarios": ["13:00", "21:30"], "notify_minutes": 5},
    {"nome": "Flame Maiden", "local": "Firelands", "frequencia": "evento_firelands", "horarios_sabado": ["15:30"], "horarios_domingo": ["20:30"], "notify_minutes": 5},
    {"nome": "King Devil Bird", "local": None, "frequencia": "diaria", "horarios": ["11:15", "21:15"], "notify_minutes": 5},
    {"nome": "Queen Chaos Cara", "local": None, "frequencia": "diaria", "horarios": ["13:15", "23:15"], "notify_minutes": 5},
    {"nome": "Hells Gate", "local": None, "frequencia": "diaria", "horarios": ["12:00", "20:00"], "notify_minutes": 5},
    {"nome": "Battlegrounds", "local": None, "frequencia": "diaria", "horarios": ["12:30", "21:30"], "notify_minutes": 5},
    {"nome": "Infernal Abyss - Firelands", "local": None, "frequencia": "evento_firelands", "horarios_sabado": ["15:30"], "horarios_domingo": ["20:30"], "notify_minutes": 5},
    {"nome": "Crystal Cave - Expedition", "local": "Ricartem", "frequencia": "terca_quinta", "horarios": ["13:00", "21:00"], "notify_minutes": 5},
    {"nome": "Bless Castle", "local": None, "frequencia": "semanal", "dias_semana": [0], "horarios": ["10:00"], "notify_minutes": 30},
]


def get_boss_times_for_date(boss, date_obj):
    dow = date_obj.weekday()  # 0=segunda ... 6=domingo
    freq = boss["frequencia"]
    if freq == "diaria":
        return boss.get("horarios", [])
    if freq in ("fim_de_semana", "evento_firelands"):
        if dow == 5:  # sabado
            return boss.get("horarios_sabado", [])
        if dow == 6:  # domingo
            return boss.get("horarios_domingo", [])
        return []
    if freq == "terca_quinta":
        if dow in (1, 3):  # terca=1, quinta=3
            return boss.get("horarios", [])
        return []
    if freq == "semanal":
        # dias_semana usa convencao JS (0=domingo...6=sabado); converte pra Python (0=segunda...6=domingo)
        js_dow = 0 if dow == 6 else dow + 1
        if js_dow in boss.get("dias_semana", []):
            return boss.get("horarios", [])
        return []
    return []


def get_next_occurrence(boss, now):
    for add_days in range(0, 9):
        d = (now + timedelta(days=add_days)).replace(hour=0, minute=0, second=0, microsecond=0)
        for t in get_boss_times_for_date(boss, d):
            h, m = map(int, t.split(":"))
            candidate = d.replace(hour=h, minute=m)
            if candidate > now:
                return candidate
    return None


def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_log(keys):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(keys, f)


def send_push(title, message):
    if not ONESIGNAL_APP_ID or not ONESIGNAL_REST_API_KEY:
        print("OneSignal não configurado (faltam variáveis de ambiente). Pulando envio.")
        return
    resp = requests.post(
        "https://api.onesignal.com/notifications",
        headers={
            "Authorization": f"Key {ONESIGNAL_REST_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "app_id": ONESIGNAL_APP_ID,
            "target_channel": "push",
            "included_segments": ["Subscribed Users"],
            "headings": {"en": title, "pt": title},
            "contents": {"en": message, "pt": message},
        },
        timeout=20,
    )
    print("OneSignal status:", resp.status_code, resp.text[:300])


def main():
    now = datetime.now(TZ)
    log = load_log()
    log_set = set(log)

    # Garante que o arquivo exista desde a primeira execução (mesmo vazio),
    # senão o "git add" no workflow falha por o arquivo não existir ainda.
    if not os.path.exists(LOG_FILE):
        save_log(log)

    # Agrupa bosses/eventos que nascem no mesmo horário E têm o mesmo
    # tempo de aviso (pra não misturar avisos de 5min com o de 30min)
    by_group = {}
    for boss in SCHEDULED_BOSSES:
        next_occ = get_next_occurrence(boss, now)
        if not next_occ:
            continue
        notify_minutes = boss.get("notify_minutes", DEFAULT_NOTIFY_MINUTES)
        minutes_until = (next_occ - now).total_seconds() / 60
        if notify_minutes - 0.5 <= minutes_until <= notify_minutes + 0.5:
            key = f"{next_occ.strftime('%Y-%m-%d %H:%M')}|{boss['nome']}"
            if key in log_set:
                continue
            group_key = (next_occ.strftime("%Y-%m-%d %H:%M"), notify_minutes)
            by_group.setdefault(group_key, []).append((boss["nome"], key))

    if not by_group:
        print("Nenhum boss/evento no intervalo de aviso agora.")
        return

    new_keys = []
    for (time_str, notify_minutes), entries in by_group.items():
        names = [n for n, k in entries]
        keys = [k for n, k in entries]
        hhmm = time_str.split(" ")[1]

        if len(names) == 1:
            title = f"{names[0]} em {notify_minutes} minutos"
            message = f"Vai nascer às {hhmm}"
        else:
            title = f"{len(names)} eventos em {notify_minutes} minutos"
            message = f"{', '.join(names)} vão nascer às {hhmm}"

        send_push(title, message)
        new_keys.extend(keys)

    log.extend(new_keys)
    # mantem só os ultimos 300 registros pra nao crescer pra sempre
    log = log[-300:]
    save_log(log)
    print(f"{len(new_keys)} notificação(ões) enviada(s).")


if __name__ == "__main__":
    main()
