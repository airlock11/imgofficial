#!/usr/bin/env python3
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "odds-data.json"
API = "https://api.oddspapi.io/v4"
KEY = (os.environ.get("ODDSPAPI_KEY") or "").strip()
UA = "IMG-Sports-Odds-Updater/2.0 (+https://imgofficial.com)"

# Stable tournament IDs published by OddsPapi.
TARGETS = {
    "nba": {"tournament_id": 132, "sport_id": 11},
    "nfl": {"tournament_id": 31, "sport_id": 14},
    "epl": {"tournament_id": 17, "sport_id": 10},
    "laliga": {"tournament_id": 8, "sport_id": 10},
}

def get_json(path, params):
    query = dict(params)
    query["apiKey"] = KEY
    url = API + path + "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))

def as_list(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "items", "fixtures", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        if payload.get("fixtureId"):
            return [payload]
    return []

def current_price(node):
    if not isinstance(node, dict):
        return None
    player = (node.get("players") or {}).get("0")
    if not isinstance(player, dict):
        return None
    if player.get("active") is False:
        return None
    price = player.get("price")
    return price if isinstance(price, (int, float)) else None

def market_outcomes(book, market_id):
    markets = (book or {}).get("markets") or {}
    market = markets.get(str(market_id))
    if not isinstance(market, dict) or market.get("marketActive") is False:
        return {}
    return market.get("outcomes") or {}

def soccer_moneyline(book):
    outcomes = market_outcomes(book, 101)
    return (
        current_price(outcomes.get("101")),
        current_price(outcomes.get("102")),
        current_price(outcomes.get("103")),
    )

def basketball_moneyline(book):
    outcomes = market_outcomes(book, 111)
    return current_price(outcomes.get("111")), current_price(outcomes.get("112"))

def generic_moneyline(book, sport_id):
    if sport_id == 10:
        home, draw, away = soccer_moneyline(book)
        return home, away, draw
    if sport_id in (11, 14):
        home, away = basketball_moneyline(book)
        if home is not None or away is not None:
            return home, away, None

    # Fallback: find a two- or three-way market whose bookmaker outcome IDs
    # clearly identify home/away/draw.
    for market in ((book or {}).get("markets") or {}).values():
        outcomes = market.get("outcomes") or {}
        found = {}
        for outcome in outcomes.values():
            player = (outcome.get("players") or {}).get("0") or {}
            label = str(player.get("bookmakerOutcomeId") or "").lower()
            price = current_price(outcome)
            if price is None:
                continue
            if label in ("home", "1"):
                found["home"] = price
            elif label in ("away", "2"):
                found["away"] = price
            elif label in ("draw", "x"):
                found["draw"] = price
        if "home" in found and "away" in found:
            return found.get("home"), found.get("away"), found.get("draw")
    return None, None, None

def main_line_value(book, kind):
    candidates = []
    for market in ((book or {}).get("markets") or {}).values():
        if market.get("marketActive") is False:
            continue
        for outcome in (market.get("outcomes") or {}).values():
            player = (outcome.get("players") or {}).get("0") or {}
            if player.get("active") is False or player.get("price") is None:
                continue
            label = str(player.get("bookmakerOutcomeId") or "").lower()
            if kind == "total" and ("/over" in label or "/under" in label):
                m = label.split("/", 1)[0].strip()
                try:
                    value = float(m)
                except Exception:
                    continue
                candidates.append((bool(player.get("mainLine")), value))
            elif kind == "spread" and ("/home" in label or "/away" in label):
                m = label.split("/", 1)[0].strip()
                try:
                    value = float(m)
                except Exception:
                    continue
                candidates.append((bool(player.get("mainLine")), value))
    if not candidates:
        return "—"
    main = [v for is_main, v in candidates if is_main]
    values = main or [v for _, v in candidates]
    value = values[0]
    return str(int(value)) if float(value).is_integer() else str(value)

def fixture_map():
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=2)
    mapping = {}

    # One fixture request per sport. The API permits sportId + a short date range.
    for sport_id in (10, 11, 14):
        payload = get_json("/fixtures", {
            "sportId": sport_id,
            "from": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "statusId": 0,
            "hasOdds": "true",
            "bookmakers": "bet365",
        })
        for fixture in as_list(payload):
            tid = fixture.get("tournamentId")
            fid = fixture.get("fixtureId")
            if not fid or tid not in {x["tournament_id"] for x in TARGETS.values()}:
                continue
            mapping[str(fid)] = fixture
    return mapping

def normalize(row, fixture):
    book = (row.get("bookmakerOdds") or {}).get("bet365")
    if not isinstance(book, dict) or book.get("suspended") is True:
        return None

    sport_id = int(row.get("sportId") or fixture.get("sportId") or 0)
    home, away, draw = generic_moneyline(book, sport_id)
    spread = main_line_value(book, "spread")
    total = main_line_value(book, "total")

    if home is None and away is None and spread == total == "—":
        return None

    provider = {
        "provider": "Bet365",
        "details": spread,
        "total": total,
        "home": "—" if home is None else str(home),
        "away": "—" if away is None else str(away),
    }
    if draw is not None:
        provider["draw"] = str(draw)

    return {
        "eventId": str(row.get("fixtureId") or fixture.get("fixtureId") or ""),
        "date": row.get("startTime") or fixture.get("startTime") or "",
        "home": fixture.get("participant1Name") or fixture.get("participant1ShortName") or "Home",
        "away": fixture.get("participant2Name") or fixture.get("participant2ShortName") or "Away",
        "homeLogo": "",
        "awayLogo": "",
        "oddsList": [provider],
    }

def main():
    if not KEY:
        print("ODDSPAPI_KEY is not configured; preserving current odds-data.json")
        return

    errors = {}
    leagues = {}

    try:
        fixtures = fixture_map()
    except Exception as exc:
        print(json.dumps({"updated": False, "error": "fixture lookup failed: " + str(exc)[:180]}))
        return

    try:
        payload = get_json("/odds-by-tournaments", {
            "tournamentIds": ",".join(str(TARGETS[k]["tournament_id"]) for k in TARGETS),
            "bookmakers": "bet365",
            "language": "en",
            "verbosity": 3,
            "oddsFormat": "decimal",
        })
        rows = as_list(payload)
    except Exception as exc:
        print(json.dumps({"updated": False, "error": "odds lookup failed: " + str(exc)[:180]}))
        return

    by_tid = {v["tournament_id"]: k for k, v in TARGETS.items()}
    for row in rows:
        tid = row.get("tournamentId")
        key = by_tid.get(tid)
        if not key:
            continue
        fixture = fixtures.get(str(row.get("fixtureId"))) or row
        item = normalize(row, fixture)
        if item:
            leagues.setdefault(key, []).append(item)

    for key in list(leagues):
        leagues[key] = sorted(leagues[key], key=lambda x: x.get("date") or "")[:12]

    if not leagues:
        print(json.dumps({"updated": False, "message": "No current Bet365 odds returned"}))
        return

    data = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provider": "OddsPapi",
        "bookmaker": "Bet365",
        "leagues": leagues,
        "errors": errors,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({
        "updated": True,
        "provider": "OddsPapi",
        "leagues": {k: len(v) for k, v in leagues.items()},
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
