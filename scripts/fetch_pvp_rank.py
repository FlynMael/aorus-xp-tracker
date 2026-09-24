import json
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

API_URL = "https://aorus-xp-tracker.vercel.app/api/data"
TZ = ZoneInfo("America/Sao_Paulo")
OUT_FILE = "data/pvp_rank.json"
TOP_N = 30
