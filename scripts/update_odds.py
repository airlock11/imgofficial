#!/usr/bin/env python3
import json
import os
import re
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
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
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        detail = body[:500] if body else str(exc)
        raise RuntimeError(f"HTTP {exc.code}: {detail}")

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

def direct_price(book, market_id, outcome_id):
    market = ((book or {}).get("markets") or {}).get(str(market_id)) or {}
    outcome = (market.get("outcomes") or {}).get(str(outcome_id)) or {}
    return current_price(outcome)

def participant_maps(sport_ids):
    maps = {}
    for sport_id in sorted(set(sport_ids)):
        try:
            time.sleep(1.1)
            payload = get_json("/participants", {"sportId": sport_id, "language": "en"})
            if isinstance(payload, dict):
                maps[sport_id] = {str(k): str(v) for k, v in payload.items()}
        except Exception as exc:
            print(json.dumps({"participants": sport_id, "error": str(exc)[:180]}, ensure_ascii=False))
    return maps

def market_catalog():
    try:
        time.sleep(1.1)
        payload = get_json("/markets", {"language": "en"})
        if not isinstance(payload, list):
            return {}
        return {str(x.get("marketId")): x for x in payload if isinstance(x, dict) and x.get("marketId") is not None}
    except Exception as exc:
        print(json.dumps({"markets_catalog": "unavailable", "error": str(exc)[:180]}, ensure_ascii=False))
        return {}


def market_outcomes(book, market_id):
    markets = (book or {}).get("markets") or {}
    market = markets.get(str(market_id))
    if not isinstance(market, dict) or market.get("marketActive") is False:
        return {}
    return market.get("outcomes") or {}

def generic_moneyline(book, sport_id):
    # Stable result-market IDs documented by OddsPapi.
    if sport_id == 10:
        home = direct_price(book, 101, 101)
        draw = direct_price(book, 101, 102)
        away = direct_price(book, 101, 103)
        if home is not None or away is not None:
            return home, away, draw

    if sport_id == 11:
        for market_id in (111, 141):
            home = direct_price(book, market_id, market_id)
            away = direct_price(book, market_id, market_id + 1)
            if home is not None or away is not None:
                return home, away, None

    if sport_id == 14:
        home = direct_price(book, 141, 141)
        away = direct_price(book, 141, 142)
        if home is not None or away is not None:
            return home, away, None

    # Fallback for other books/sports that provide textual outcome IDs.
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
            return found.get("home"), found.get("away"), found.get("draw")
    return None, None, None

def main_line_value(book, kind, catalog=None):
    candidates = []
    for market_id, market in ((book or {}).get("markets") or {}).items():
        if not isinstance(market, dict) or market.get("marketActive") is False:
            continue

        info = (catalog or {}).get(str(market_id)) or {}
        name = str(info.get("marketName") or "").lower()
        is_total = ("total" in name or "over/under" in name)
        is_spread = ("handicap" in name or "spread" in name) and not is_total

        active_players = []
        for outcome in (market.get("outcomes") or {}).values():
            if not isinstance(outcome, dict):
                continue
            player = (outcome.get("players") or {}).get("0") or {}
            if player.get("active") is not False and isinstance(player.get("price"), (int, float)):
                active_players.append(player)

        if not active_players:
            continue

        if (kind == "total" and is_total) or (kind == "spread" and is_spread):
            handicap = info.get("handicap")
            if handicap is None:
                nums = []
                for player in active_players:
                    label = str(player.get("bookmakerOutcomeId") or "")
                    nums.extend(re.findall(r"[-+]?\d+(?:\.\d+)?", label))
                if nums:
                    try:
                        handicap = float(nums[0])
                    except Exception:
                        handicap = None
            if handicap is not None:
                candidates.append((any(bool(p.get("mainLine")) for p in active_players), handicap))

    if not candidates:
        return "—"

    main = [v for is_main, v in candidates if is_main]
    value = (main or [v for _, v in candidates])[0]
    try:
        number = float(value)
        return str(int(number)) if number.is_integer() else str(number)
    except Exception:
        return str(value)

def normalize(row, participants=None, catalog=None):
    book = (row.get("bookmakerOdds") or {}).get("bet365")
    if not isinstance(book, dict) or book.get("suspended") is True or book.get("bookmakerIsActive") is False:
        return None

    sport_id = int(row.get("sportId") or 0)
    home, away, draw = generic_moneyline(book, sport_id)
    spread = main_line_value(book, "spread", catalog)
    total = main_line_value(book, "total", catalog)

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

    p1id = row.get("participant1Id")
    p2id = row.get("participant2Id")
    sport_names = (participants or {}).get(sport_id, {})
    p1 = row.get("participant1Name") or row.get("participant1ShortName") or sport_names.get(str(p1id))
    p2 = row.get("participant2Name") or row.get("participant2ShortName") or sport_names.get(str(p2id))

    return {
        "eventId": str(row.get("fixtureId") or ""),
        "date": row.get("startTime") or "",
        "home": p1 or ("Home " + str(p1id) if p1id is not None else "Home"),
        "away": p2 or ("Away " + str(p2id) if p2id is not None else "Away"),
        "participant1Id": p1id,
        "participant2Id": p2id,
        "homeLogo": "",
        "awayLogo": "",
        "oddsList": [provider],
    }

def main():
    if not KEY:
        print("ODDSPAPI_KEY is not configured; preserving current odds-data.json")
        return

    # /account is unmetered and remains available even when the monthly
    # allowance is exhausted. Log only usage counts, never the key.
    try:
        account = get_json("/account", {})
        subscription = account.get("subscription") if isinstance(account, dict) else None
        if not isinstance(subscription, dict):
            subscription = account if isinstance(account, dict) else {}
        print(json.dumps({
            "quota_limit": subscription.get("request_limit"),
            "quota_used": subscription.get("request_count"),
        }, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"quota_check": "unavailable", "detail": str(exc)[:220]}, ensure_ascii=False))

    try:
        payload = get_json("/odds-by-tournaments", {
            "tournamentIds": ",".join(str(TARGETS[k]["tournament_id"]) for k in TARGETS),
            "bookmaker": "bet365",
            "language": "en",
            "verbosity": 3,
            "oddsFormat": "decimal",
        })
        rows = as_list(payload)
    except Exception as exc:
        raise RuntimeError("Bet365 odds lookup failed: " + str(exc)[:500])

    bookmaker_keys = sorted({
        str(key)
        for row in rows[:25]
        for key in ((row.get("bookmakerOdds") or {}).keys())
    })
    print(json.dumps({
        "odds_rows": len(rows),
        "requested_bookmaker": "bet365",
        "returned_bookmakers": bookmaker_keys[:20],
    }, ensure_ascii=False))

    sport_ids = [int(row.get("sportId")) for row in rows if row.get("sportId") is not None]
    participants = participant_maps(sport_ids)
    catalog = market_catalog()

    leagues = {}
    by_tid = {v["tournament_id"]: k for k, v in TARGETS.items()}
    bet365_rows = 0

    for row in rows:
        tid = row.get("tournamentId")
        key = by_tid.get(tid)
        if not key:
            continue
        item = normalize(row, participants, catalog)
        if item:
            bet365_rows += 1
            leagues.setdefault(key, []).append(item)

    for key in list(leagues):
        leagues[key] = sorted(leagues[key], key=lambda x: x.get("date") or "")[:12]

    if not leagues:
        print(json.dumps({
            "updated": False,
            "message": "No current Bet365 odds returned",
            "odds_rows": len(rows),
            "bet365_rows": bet365_rows,
        }, ensure_ascii=False))
        return

    data = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provider": "OddsPapi",
        "bookmaker": "Bet365",
        "leagues": leagues,
        "errors": {},
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({
        "updated": True,
        "provider": "OddsPapi",
        "leagues": {k: len(v) for k, v in leagues.items()},
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
