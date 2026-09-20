#!/usr/bin/env python3
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "odds-meta.json"
API = "https://api.oddspapi.io/v4"
KEY = (os.environ.get("ODDSPAPI_KEY") or "").strip()
UA = "IMG-Sports-Odds-Metadata/1.0 (+https://imgofficial.com)"
SPORT_IDS = (10, 11, 14)

def get_json(path, params):
    query = dict(params)
    query["apiKey"] = KEY
    req = urllib.request.Request(
        API + path + "?" + urllib.parse.urlencode(query),
        headers={"User-Agent": UA, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        raise RuntimeError(f"HTTP {exc.code}: {(body or str(exc))[:400]}")

def main():
    if not KEY:
        print("ODDSPAPI_KEY is not configured")
        return

    try:
        old = json.loads(OUT.read_text("utf-8"))
    except Exception:
        old = {"participants": {}}

    participants = old.get("participants") if isinstance(old, dict) else {}
    if not isinstance(participants, dict):
        participants = {}

    for index, sport_id in enumerate(SPORT_IDS):
        if index:
            time.sleep(1.2)
        payload = get_json("/participants", {"sportId": sport_id, "language": "en"})
        if isinstance(payload, dict):
            participants[str(sport_id)] = {str(k): str(v) for k, v in payload.items()}
            print(json.dumps({"sport_id": sport_id, "participants": len(payload)}))

    out = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "participants": participants,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", "utf-8")

if __name__ == "__main__":
    main()
