#!/usr/bin/env python3
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "wta-live.json"
LIVE_URL = "https://api.sofascore.com/api/v1/sport/tennis/events/live"
WTA_VERIFY = "https://www.wtatennis.com/scores/"
UA = "Mozilla/5.0 (compatible; IMG-Sports-WTA-Live/2.0; +https://imgofficial.com)"

def fetch_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))

def normalize_point(value):
    text = str(value if value is not None else "").strip().upper()
    if text in {"A", "ADV", "AV"}:
        return "AD"
    if text in {"0", "15", "30", "40", "AD"}:
        return text
    return text or "—"

def plain_games(value):
    try:
        return int(re.match(r"\d+", str(value)).group(0))
    except Exception:
        return None

def score_parts(score):
    score = score if isinstance(score, dict) else {}
    sets = []
    raw_sets = []
    for i in range(1, 6):
        value = score.get(f"period{i}")
        if value in (None, ""):
            continue
        tie = score.get(f"period{i}TieBreak")
        display = str(value)
        if tie not in (None, ""):
            display += f"({tie})"
        sets.append(display)
        raw_sets.append(plain_games(value))
    return {
        "sets": sets,
        "rawSets": raw_sets,
        "point": normalize_point(score.get("point")),
        "current": score.get("current"),
    }

def set_is_complete(a, b):
    if a is None or b is None:
        return False
    high, low = max(a, b), min(a, b)
    return high >= 6 and (high - low >= 2 or high == 7)

def sets_won(own, opp, current_set):
    won = 0
    for i, (a, b) in enumerate(zip(own, opp), start=1):
        if i >= current_set:
            break
        if a is not None and b is not None and a > b and set_is_complete(a, b):
            won += 1
    return won

def current_set_number(away_raw, home_raw, status_description):
    count = max(len(away_raw), len(home_raw))
    m = re.search(r"\b([1-5])(?:st|nd|rd|th)\s+set\b", str(status_description or ""), re.I)
    if m:
        return int(m.group(1))
    if count:
        # While in progress, the last reported period is the current set unless
        # all reported sets are clearly complete, in which case the next set is current.
        last_a = away_raw[count - 1] if len(away_raw) >= count else None
        last_b = home_raw[count - 1] if len(home_raw) >= count else None
        if set_is_complete(last_a, last_b):
            return min(count + 1, 5)
        return count
    return 1

def main():
    payload = fetch_json(LIVE_URL)
    events = payload.get("events", []) if isinstance(payload, dict) else []
    games = []

    for e in events:
        tournament = e.get("tournament") or {}
        category = tournament.get("category") or {}
        category_slug = str(category.get("slug") or category.get("name") or "").strip().lower()
        if category_slug != "wta":
            continue

        status = e.get("status") or {}
        status_type = str(status.get("type") or "").lower()
        if status_type != "inprogress":
            continue

        away_team = e.get("awayTeam") or {}
        home_team = e.get("homeTeam") or {}
        away_name = str(away_team.get("shortName") or away_team.get("name") or "").strip()
        home_name = str(home_team.get("shortName") or home_team.get("name") or "").strip()
        if not away_name or not home_name:
            continue

        away = score_parts(e.get("awayScore") or {})
        home = score_parts(e.get("homeScore") or {})
        status_description = str(status.get("description") or "Live").strip()
        current_set = current_set_number(away["rawSets"], home["rawSets"], status_description)

        away_current_games = 0
        home_current_games = 0
        if len(away["rawSets"]) >= current_set and away["rawSets"][current_set - 1] is not None:
            away_current_games = away["rawSets"][current_set - 1]
        if len(home["rawSets"]) >= current_set and home["rawSets"][current_set - 1] is not None:
            home_current_games = home["rawSets"][current_set - 1]

        away_sets_won = sets_won(away["rawSets"], home["rawSets"], current_set)
        home_sets_won = sets_won(home["rawSets"], away["rawSets"], current_set)

        unique = tournament.get("uniqueTournament") or {}
        tournament_name = str(unique.get("name") or tournament.get("name") or "WTA")
        round_name = str((e.get("roundInfo") or {}).get("name") or "").strip()
        court = str(e.get("court") or e.get("courtName") or "").strip()

        game = {
            "eventId": "wta-live-" + str(e.get("id") or e.get("customId") or len(games) + 1),
            "date": datetime.fromtimestamp(e.get("startTimestamp"), timezone.utc).isoformat() if e.get("startTimestamp") else "",
            "displayTime": tournament_name,
            "away": away_name,
            "home": home_name,
            "awayScore": " ".join(away["sets"]) + ((" · " + away["point"]) if away["point"] != "—" else ""),
            "homeScore": " ".join(home["sets"]) + ((" · " + home["point"]) if home["point"] != "—" else ""),
            "awaySets": away["sets"],
            "homeSets": home["sets"],
            "awayPoint": away["point"],
            "homePoint": home["point"],
            "currentSet": current_set,
            "awayCurrentSetGames": away_current_games,
            "homeCurrentSetGames": home_current_games,
            "awaySetsWon": away_sets_won,
            "homeSetsWon": home_sets_won,
            "round": round_name,
            "court": court,
            "status": " · ".join(x for x in [status_description, round_name, court] if x),
            "state": "live",
            "eventOnly": False,
            "title": tournament_name,
            "sourceName": "Structured live tennis feed",
            "sourceUrl": LIVE_URL,
            "verificationSource": "WTA Official Scores",
            "verificationUrl": WTA_VERIFY,
        }
        games.append(game)

    result = {
        "special": True,
        "league": "WTA Tour",
        "live": bool(games),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceName": "Structured live tennis feed",
        "sourceUrl": LIVE_URL,
        "verificationSource": "WTA Official Scores",
        "verificationUrl": WTA_VERIFY,
        "note": "GitHub-generated WTA live data with current game points, current set number, current-set games, per-set scores and sets won stored separately.",
        "games": games,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print("WTA live matches:", len(games))
    for game in games:
        print(
            "LIVE",
            game["away"], game["awayPoint"], game["awaySets"],
            "vs",
            game["home"], game["homePoint"], game["homeSets"],
            "| set", game["currentSet"],
            "| current games", game["awayCurrentSetGames"], "-", game["homeCurrentSetGames"],
        )

if __name__ == "__main__":
    main()
