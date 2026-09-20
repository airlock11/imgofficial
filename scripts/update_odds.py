#!/usr/bin/env python3
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "odds-data.json"
API = "https://api.odds-api.io/v3"
KEY = (os.environ.get("ODDS_API_IO_KEY") or "").strip()
UA = "IMG-Sports-Odds-Updater/1.0 (+https://imgofficial.com)"

TARGETS = [
    {"key": "nba", "sport": "basketball", "league": "usa-nba"},
    {"key": "nfl", "sport": "american-football", "league": "usa-nfl"},
    {"key": "epl", "sport": "football", "league": "england-premier-league"},
    {"key": "laliga", "sport": "football", "league": "spain-la-liga"},
    {"key": "seriea", "sport": "football", "league": "italy-serie-a"},
    {"key": "bundesliga", "sport": "football", "league": "germany-bundesliga"},
    {"key": "champions", "sport": "football", "league": "uefa-champions-league"},
]

def get_json(path, params):
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        API + path + "?" + query,
        headers={"User-Agent": UA, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))

def as_list(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if payload.get("id") is not None and payload.get("bookmakers") is not None:
            return [payload]
        for key in ("data", "items", "events", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []

def market(markets, names):
    wanted = {x.lower() for x in names}
    for item in markets or []:
        name = str(item.get("name") or item.get("label") or "").lower()
        if name in wanted:
            odds = item.get("odds") or []
            return odds[0] if odds and isinstance(odds[0], dict) else {}
    return {}

def value(v):
    if v is None or v == "":
        return "—"
    return str(v)

def normalize(event):
    bookmakers = event.get("bookmakers") or {}
    markets = bookmakers.get("Bet365") or bookmakers.get("bet365") or []
    if not markets:
        return None

    ml = market(markets, ("ML", "Moneyline", "Match Result"))
    spread = market(markets, ("Spread", "Spreads", "Handicap"))
    totals = market(markets, ("Totals", "Total", "Over/Under"))

    home = value(ml.get("home"))
    away = value(ml.get("away"))
    line = value(spread.get("hdp"))
    total = value(totals.get("hdp"))

    if home == away == line == total == "—":
        return None

    return {
        "eventId": str(event.get("id") or ""),
        "date": event.get("date") or "",
        "home": event.get("home") or "Home",
        "away": event.get("away") or "Away",
        "homeLogo": "",
        "awayLogo": "",
        "oddsList": [{
            "provider": "Bet365",
            "details": line,
            "total": total,
            "home": home,
            "away": away,
        }],
    }

def main():
    if not KEY:
        print("ODDS_API_IO_KEY is not configured; preserving current odds-data.json")
        return

    leagues = {}
    errors = {}

    for target in TARGETS:
        try:
            events = get_json("/events", {
                "apiKey": KEY,
                "sport": target["sport"],
                "league": target["league"],
                "status": "pending",
                "limit": 4,
            })
            events = as_list(events)
            if not events:
                continue

            ids = [str(e.get("id")) for e in events if e.get("id") is not None][:10]
            if not ids:
                continue

            payload = get_json("/odds/multi", {
                "apiKey": KEY,
                "eventIds": ",".join(ids),
                "bookmakers": "Bet365",
            })
            rows = [normalize(x) for x in as_list(payload)]
            rows = [x for x in rows if x]
            if rows:
                leagues[target["key"]] = rows
        except Exception as exc:
            errors[target["key"]] = str(exc)[:180]

    # Only replace the public cache when at least one real Bet365 line was found.
    if not leagues:
        print(json.dumps({"updated": False, "errors": errors}, ensure_ascii=False))
        return

    data = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provider": "Odds-API.io",
        "bookmaker": "Bet365",
        "leagues": leagues,
        "errors": errors,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({
        "updated": True,
        "leagues": {k: len(v) for k, v in leagues.items()},
        "errors": errors,
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
