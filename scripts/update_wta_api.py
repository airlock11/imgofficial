#!/usr/bin/env python3
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "wta-live.json"
BASE = "https://api.api-tennis.com/tennis/"
KEY = os.environ["API_TENNIS_KEY"]
UA = "IMG-Sports-WTA/2.0"

def get_json(params):
    query = dict(params)
    query["APIkey"] = KEY
    url = BASE + "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)

def is_wta(row):
    typ = str(row.get("event_type_type") or "").strip().lower()
    return typ.startswith("wta ") or typ in {"wta", "wta singles", "wta doubles"}

def parse_pair(value):
    parts = [x.strip() for x in re.split(r"\s*-\s*", str(value or "")) if x.strip()]
    return parts[:2] if len(parts) >= 2 else []

def latest_point(row):
    # API-Tennis exposes the current game score directly. Use it first.
    direct = parse_pair(row.get("event_game_result"))
    if direct and direct != ["0", "0"]:
        return direct

    # If event_game_result is empty/stale, derive the latest point from point-by-point.
    p2p = row.get("pointbypoint")
    if not isinstance(p2p, list):
        return ["—", "—"]
    for game in reversed(p2p):
        points = game.get("points") if isinstance(game, dict) else None
        if not isinstance(points, list) or not points:
            continue
        score = parse_pair(points[-1].get("score"))
        if score:
            return score
    return ["—", "—"]

def set_scores(row):
    first, second = [], []
    scores = row.get("scores")
    if isinstance(scores, list):
        ordered = sorted(
            [x for x in scores if isinstance(x, dict)],
            key=lambda x: int(re.sub(r"\D", "", str(x.get("score_set") or "0")) or 0)
        )
        for s in ordered[:5]:
            first.append(str(s.get("score_first") if s.get("score_first") is not None else "—"))
            second.append(str(s.get("score_second") if s.get("score_second") is not None else "—"))
    return first, second

def current_set(status, sets):
    m = re.search(r"set\s*(\d+)", str(status or ""), re.I)
    if m:
        return max(1, int(m.group(1)))
    return max(1, len(sets))

def sets_won(a, b, current):
    won = 0
    for i, (x, y) in enumerate(zip(a, b), start=1):
        if i >= current:
            break
        try:
            xv = int(re.match(r"\d+", str(x)).group())
            yv = int(re.match(r"\d+", str(y)).group())
        except Exception:
            continue
        high, low = max(xv, yv), min(xv, yv)
        complete = high >= 6 and (high - low >= 2 or high == 7)
        if complete and xv > yv:
            won += 1
    return won

def normalize_state(row):
    status = str(row.get("event_status") or "").strip()
    low = status.lower()
    if "suspend" in low:
        return "suspended"
    if "warm" in low or "on court" in low:
        return "warmup"
    if str(row.get("event_live") or "") == "1":
        return "live"
    if "finish" in low or str(row.get("event_final_result") or "").strip() not in {"", "-", "0 - 0"}:
        return "final"
    return "scheduled"

def normalize(row):
    away = str(row.get("event_first_player") or "Player 1").strip()
    home = str(row.get("event_second_player") or "Player 2").strip()
    away_sets, home_sets = set_scores(row)
    state = normalize_state(row)
    point = latest_point(row) if state in {"live","suspended","warmup"} else ["—","—"]
    status = str(row.get("event_status") or ("Finished" if state=="final" else "Scheduled")).strip() or ("Finished" if state=="final" else "Scheduled")
    current = current_set(status, away_sets)

    def num_at(values, idx):
        if idx < 0 or idx >= len(values):
            return 0
        m = re.match(r"\d+", str(values[idx]))
        return int(m.group()) if m else 0

    round_name = str(row.get("tournament_round") or "").strip()
    tournament = str(row.get("tournament_name") or "WTA").strip()
    event_key = str(row.get("event_key") or "").strip()
    date = str(row.get("event_date") or "").strip()
    time = str(row.get("event_time") or "").strip()
    dt = datetime.now(timezone.utc).isoformat()
    if date and time:
        dt = date + "T" + time + ":00"

    return {
        "eventId": "api-tennis-wta-" + (event_key or re.sub(r"[^a-z0-9]+", "-", (away+"-"+home).lower()).strip("-")),
        "apiEventKey": event_key,
        "date": dt,
        "displayTime": tournament,
        "away": away,
        "home": home,
        "awayLogo": row.get("event_first_player_logo") or "",
        "homeLogo": row.get("event_second_player_logo") or "",
        "awayScore": " ".join(away_sets) + ((" · " + point[0]) if point[0] != "—" else ""),
        "homeScore": " ".join(home_sets) + ((" · " + point[1]) if point[1] != "—" else ""),
        "awaySets": away_sets,
        "homeSets": home_sets,
        "awayPoint": point[0],
        "homePoint": point[1],
        "currentSet": current,
        "awayCurrentSetGames": num_at(away_sets, current-1),
        "homeCurrentSetGames": num_at(home_sets, current-1),
        "awaySetsWon": sets_won(away_sets, home_sets, current),
        "homeSetsWon": sets_won(home_sets, away_sets, current),
        "round": round_name,
        "court": "",
        "status": " · ".join(x for x in [status, round_name] if x),
        "state": state,
        "eventOnly": False,
        "title": tournament,
        "eventType": str(row.get("event_type_type") or ""),
        "serve": row.get("event_serve"),
        "sourceName": "API-Tennis",
        "sourceUrl": "https://api-tennis.com/",
        "verificationSource": "API-Tennis",
        "verificationUrl": "https://api-tennis.com/",
    }

def main():
    live_payload = get_json({"method": "get_livescore", "timezone": "UTC"})
    if int(live_payload.get("success") or 0) != 1:
        raise RuntimeError("API-Tennis livescore request failed")

    today = datetime.now(timezone.utc).date()
    fixture_payload = get_json({
        "method": "get_fixtures",
        "date_start": (today - timedelta(days=1)).isoformat(),
        "date_stop": (today + timedelta(days=2)).isoformat(),
        "timezone": "UTC",
    })
    if int(fixture_payload.get("success") or 0) != 1:
        fixture_payload = {"result": []}

    live_rows = [x for x in (live_payload.get("result") or []) if isinstance(x, dict) and is_wta(x)]
    fixture_rows = [x for x in (fixture_payload.get("result") or []) if isinstance(x, dict) and is_wta(x)]

    by_key = {}
    for row in fixture_rows:
        key = str(row.get("event_key") or "")
        if key:
            by_key[key] = row
    for row in live_rows:
        key = str(row.get("event_key") or "")
        if key:
            by_key[key] = row

    rows = list(by_key.values())
    games = [normalize(x) for x in rows]

    # Keep the payload focused: recent completed matches, current live matches,
    # and the next two days of scheduled WTA matches.
    games.sort(key=lambda g: str(g.get("date") or ""))
    finals = [g for g in games if g["state"] == "final"][-30:]
    active = [g for g in games if g["state"] in {"live","suspended","warmup"}]
    scheduled = [g for g in games if g["state"] == "scheduled"][:40]
    games = finals + active + scheduled

    out = {
        "special": True,
        "league": "WTA Tour",
        "live": bool(active),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceName": "API-Tennis",
        "sourceUrl": "https://api-tennis.com/",
        "verificationSource": "API-Tennis",
        "verificationUrl": "https://api-tennis.com/",
        "providerMatchCount": len(rows),
        "parsedMatchCount": len(games),
        "recentCount": len(finals),
        "liveCount": len(active),
        "scheduleCount": len(scheduled),
        "note": "WTA live, recent results and near-term schedule from API-Tennis. The WTA webpage scraper is used only if the API call fails.",
        "games": games,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    doubles = sum(1 for g in games if "/" in g["away"] or "/" in g["home"])
    print("API-Tennis WTA live matches:", len(games), "doubles:", doubles)
    for g in games:
        print(g["displayTime"], "|", g["away"], g["awayPoint"], g["awaySets"], "vs", g["home"], g["homePoint"], g["homeSets"], "|", g["state"])

if __name__ == "__main__":
    main()
