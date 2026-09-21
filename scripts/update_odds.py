#!/usr/bin/env python3
import json
import os
import re
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "odds-data.json"
META = ROOT / "odds-meta.json"
API = "https://api.oddspapi.io/v4"
KEY = (os.environ.get("ODDSPAPI_KEY") or "").strip()
UA = "IMG-Sports-Odds-Updater/3.0 (+https://imgofficial.com)"
THE_ODDS_KEY = (os.environ.get("ODDS_API_KEY") or "").strip()
THE_ODDS_API = "https://api.the-odds-api.com/v4"
THE_ODDS_SPORTS = {
    "nba": "basketball_nba",
    "nfl": "americanfootball_nfl",
    "epl": "soccer_epl",
    "laliga": "soccer_spain_la_liga",
}

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


def load_meta():
    try:
        data = json.loads(META.read_text("utf-8"))
        participants = data.get("participants") if isinstance(data, dict) else {}
        if not isinstance(participants, dict):
            participants = {}
        return {int(k): v for k, v in participants.items() if isinstance(v, dict)}
    except Exception:
        return {}

def save_meta_names(meta, rows):
    changed = False
    for row in rows:
        try:
            sport_id = int(row.get("sportId") or 0)
        except Exception:
            continue
        if not sport_id:
            continue
        names = meta.setdefault(sport_id, {})
        p1id, p2id = row.get("participant1Id"), row.get("participant2Id")
        p1 = row.get("participant1Name") or row.get("participant1ShortName")
        p2 = row.get("participant2Name") or row.get("participant2ShortName")
        if p1id is not None and p1 and names.get(str(p1id)) != p1:
            names[str(p1id)] = p1
            changed = True
        if p2id is not None and p2 and names.get(str(p2id)) != p2:
            names[str(p2id)] = p2
            changed = True
    if changed:
        payload = {
            "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "participants": {str(k): v for k, v in meta.items()},
        }
        META.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")

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

def main_line_value(book, kind):
    candidates = []
    for market in ((book or {}).get("markets") or {}).values():
        if not isinstance(market, dict):
            continue
        for outcome in (market.get("outcomes") or {}).values():
            if not isinstance(outcome, dict):
                continue
            player = (outcome.get("players") or {}).get("0") or {}
            if player.get("active") is False or not isinstance(player.get("price"), (int, float)):
                continue
            label = str(player.get("bookmakerOutcomeId") or "").lower().strip()

            match = None
            if kind == "total" and ("/over" in label or "/under" in label):
                match = re.search(r"^([-+]?\d+(?:\.\d+)?)", label)
            elif kind == "spread" and ("/home" in label or "/away" in label):
                match = re.search(r"^([-+]?\d+(?:\.\d+)?)", label)

            if not match:
                continue
            try:
                value = float(match.group(1))
            except Exception:
                continue
            candidates.append((bool(player.get("mainLine")), value))

    if not candidates:
        return "—"
    main = [v for is_main, v in candidates if is_main]
    value = (main or [v for _, v in candidates])[0]
    return str(int(value)) if float(value).is_integer() else str(value)

def normalize(row, participants=None):
    book = (row.get("bookmakerOdds") or {}).get("bet365")
    if not isinstance(book, dict) or book.get("suspended") is True or book.get("bookmakerIsActive") is False:
        return None

    sport_id = int(row.get("sportId") or 0)
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

def the_odds_json(sport_key):
    params = {
        "apiKey": THE_ODDS_KEY,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "decimal",
        "dateFormat": "iso",
    }
    url = THE_ODDS_API + "/sports/" + urllib.parse.quote(sport_key) + "/odds/?" + urllib.parse.urlencode(params)
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
        raise RuntimeError("The Odds API HTTP %s: %s" % (exc.code, (body or str(exc))[:400]))

def normalize_the_odds_event(row):
    books = []
    for book in row.get("bookmakers") or []:
        title = str(book.get("title") or book.get("key") or "Bookmaker").strip()
        h2h = None
        for market in book.get("markets") or []:
            if market.get("key") == "h2h":
                h2h = market
                break
        if not h2h:
            continue
        prices = {}
        for outcome in h2h.get("outcomes") or []:
            name = str(outcome.get("name") or "")
            price = outcome.get("price")
            if name and isinstance(price, (int, float)):
                prices[name] = price
        home_name = str(row.get("home_team") or "Home")
        away_name = str(row.get("away_team") or "Away")
        home = prices.get(home_name)
        away = prices.get(away_name)
        if home is None and away is None:
            continue
        provider = {
            "provider": title,
            "details": "—",
            "total": "—",
            "home": "—" if home is None else str(home),
            "away": "—" if away is None else str(away),
        }
        draw = next((v for k, v in prices.items() if k not in (home_name, away_name)), None)
        if draw is not None:
            provider["draw"] = str(draw)
        books.append(provider)
    if not books:
        return None
    return {
        "eventId": str(row.get("id") or ""),
        "date": row.get("commence_time") or "",
        "home": row.get("home_team") or "Home",
        "away": row.get("away_team") or "Away",
        "participant1Id": None,
        "participant2Id": None,
        "homeLogo": "",
        "awayLogo": "",
        "oddsList": books,
    }

def merge_the_odds(leagues):
    if not THE_ODDS_KEY:
        print("ODDS_API_KEY is not configured; keeping OddsPapi-only data")
        return
    for league, sport_key in THE_ODDS_SPORTS.items():
        try:
            rows = the_odds_json(sport_key)
        except Exception as exc:
            print(json.dumps({"the_odds_api": league, "error": str(exc)[:300]}, ensure_ascii=False))
            continue
        additions = [x for x in (normalize_the_odds_event(r) for r in rows if isinstance(r, dict)) if x]
        current = leagues.setdefault(league, [])
        for incoming in additions:
            match = next((e for e in current if
                str(e.get("home","")).casefold() == str(incoming.get("home","")).casefold() and
                str(e.get("away","")).casefold() == str(incoming.get("away","")).casefold()), None)
            if match:
                existing = {str(x.get("provider","")).casefold() for x in match.get("oddsList", [])}
                match.setdefault("oddsList", []).extend(
                    x for x in incoming["oddsList"]
                    if str(x.get("provider","")).casefold() not in existing
                )
            else:
                current.append(incoming)
        leagues[league] = sorted(current, key=lambda x: x.get("date") or "")[:20]
        print(json.dumps({
            "the_odds_api": league,
            "events": len(additions),
            "bookmakers": sorted({b["provider"] for e in additions for b in e["oddsList"]}),
        }, ensure_ascii=False))

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

    participants = load_meta()
    save_meta_names(participants, rows)

    leagues = {}
    by_tid = {v["tournament_id"]: k for k, v in TARGETS.items()}
    bet365_rows = 0

    for row in rows:
        tid = row.get("tournamentId")
        key = by_tid.get(tid)
        if not key:
            continue
        item = normalize(row, participants)
        if item:
            bet365_rows += 1
            leagues.setdefault(key, []).append(item)

    for key in list(leagues):
        leagues[key] = sorted(leagues[key], key=lambda x: x.get("date") or "")[:12]

    merge_the_odds(leagues)

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
        "provider": "OddsPapi + The Odds API",
        "bookmaker": "Multiple",
        "leagues": leagues,
        "errors": {},
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({
        "updated": True,
        "provider": "OddsPapi + The Odds API",
        "leagues": {k: len(v) for k, v in leagues.items()},
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
