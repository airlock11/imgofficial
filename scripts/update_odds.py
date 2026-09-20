#!/usr/bin/env python3
import json
import os
import re
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
    found = []
    def walk(value):
        if isinstance(value, list):
            for item in value:
                walk(item)
            return
        if not isinstance(value, dict):
            return
        if value.get("fixtureId") is not None:
            found.append(value)
            return
        for key in ("data", "items", "fixtures", "results", "odds"):
            child = value.get(key)
            if isinstance(child, (list, dict)):
                walk(child)
        if not found:
            for child in value.values():
                if isinstance(child, (list, dict)):
                    walk(child)
    walk(payload)
    return found

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

def generic_moneyline(book, sport_id):
    best = None
    for market in ((book or {}).get("markets") or {}).values():
        if not isinstance(market, dict) or market.get("marketActive") is False:
            continue
        found = {}
        for outcome in (market.get("outcomes") or {}).values():
            if not isinstance(outcome, dict):
                continue
            player = (outcome.get("players") or {}).get("0") or {}
            if player.get("active") is False:
                continue
            price = player.get("price")
            if not isinstance(price, (int, float)):
                continue
            label = str(player.get("bookmakerOutcomeId") or "").strip().lower()
            compact = label.replace(" ", "").replace("_", "").replace("-", "")
            if compact in ("home", "1", "team1", "participant1"):
                found["home"] = price
            elif compact in ("away", "2", "team2", "participant2"):
                found["away"] = price
            elif compact in ("draw", "x", "tie"):
                found["draw"] = price
        if "home" in found and "away" in found:
            score = (1 if any(
                bool(((o.get("players") or {}).get("0") or {}).get("mainLine"))
                for o in (market.get("outcomes") or {}).values()
                if isinstance(o, dict)
            ) else 0, len(found))
            if best is None or score > best[0]:
                best = (score, found)
    if best:
        found = best[1]
        return found.get("home"), found.get("away"), found.get("draw")
    return None, None, None

def main_line_value(book, kind):
    candidates = []
    for market in ((book or {}).get("markets") or {}).values():
        if not isinstance(market, dict) or market.get("marketActive") is False:
            continue
        for outcome in (market.get("outcomes") or {}).values():
            if not isinstance(outcome, dict):
                continue
            player = (outcome.get("players") or {}).get("0") or {}
            if player.get("active") is False or player.get("price") is None:
                continue
            label = str(player.get("bookmakerOutcomeId") or "").lower().strip()
            nums = re.findall(r"[-+]?\d+(?:\.\d+)?", label)
            if not nums:
                continue
            try:
                value = float(nums[0])
            except Exception:
                continue
            is_total = ("over" in label or "under" in label)
            is_spread = ("home" in label or "away" in label or "handicap" in label) and not is_total
            if (kind == "total" and is_total) or (kind == "spread" and is_spread):
                candidates.append((bool(player.get("mainLine")), value))
    if not candidates:
        return "—"
    main = [v for is_main, v in candidates if is_main]
    value = (main or [v for _, v in candidates])[0]
    return str(int(value)) if float(value).is_integer() else str(value)

def fixture_map():
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=7)
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
        "home": fixture.get("participant1Name") or fixture.get("participant1ShortName") or row.get("participant1Name") or row.get("participant1ShortName") or "Home",
        "away": fixture.get("participant2Name") or fixture.get("participant2ShortName") or row.get("participant2Name") or row.get("participant2ShortName") or "Away",
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
        raise RuntimeError("fixture lookup failed: " + str(exc)[:180])

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
        raise RuntimeError("odds lookup failed: " + str(exc)[:180])

    print(json.dumps({"fixture_rows": len(fixtures), "odds_rows": len(rows), "bookmaker": "bet365"}, ensure_ascii=False))
    by_tid = {v["tournament_id"]: k for k, v in TARGETS.items()}
    bet365_rows = 0
    for row in rows:
        tid = row.get("tournamentId")
        key = by_tid.get(tid)
        if not key:
            continue
        fixture = fixtures.get(str(row.get("fixtureId"))) or row
        item = normalize(row, fixture)
        if item:
            bet365_rows += 1
            leagues.setdefault(key, []).append(item)

    for key in list(leagues):
        leagues[key] = sorted(leagues[key], key=lambda x: x.get("date") or "")[:12]

    if not leagues:
        print(json.dumps({"updated": False, "message": "No current Bet365 odds returned", "odds_rows": len(rows), "bet365_rows": bet365_rows}, ensure_ascii=False))
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
