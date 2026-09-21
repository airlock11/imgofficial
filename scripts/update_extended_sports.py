#!/usr/bin/env python3
import json
import re
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "extended-sports-data.json"
UA = "Mozilla/5.0 (compatible; IMG-Sports-Extended/1.0; +https://imgofficial.com)"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/html,*/*"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")

def fetch_json(url):
    return json.loads(fetch(url))

def load():
    try:
        return json.loads(OUT.read_text("utf-8"))
    except Exception:
        return {"leagues": {}}

def pick(obj, *paths):
    for path in paths:
        cur = obj
        ok = True
        for key in path.split("."):
            if isinstance(cur, dict) and key in cur:
                cur = cur[key]
            else:
                ok = False
                break
        if ok and cur not in (None, ""):
            return cur
    return None

def parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None

def euroleague():
    url = "https://api-live.euroleague.net/v2/competitions/E/seasons/E2026/games"
    payload = fetch_json(url)
    rows = payload.get("data", []) if isinstance(payload, dict) else []
    games = []
    now = datetime.now(timezone.utc)
    for game in rows:
        local = pick(game, "local.club.name", "local.club.clubName", "local.clubPermanentName", "local.name")
        road = pick(game, "road.club.name", "road.club.clubName", "road.clubPermanentName", "road.name")
        if not local or not road:
            continue
        date = pick(game, "date", "startDate", "startTime", "utcDate")
        dt = parse_iso(date)
        if not dt:
            continue
        dt_utc = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        if not (now - timedelta(days=21) <= dt_utc <= now + timedelta(days=45)):
            continue
        local_score = pick(game, "local.score", "localScore", "scoreLocal", "local.points")
        road_score = pick(game, "road.score", "roadScore", "scoreRoad", "road.points")
        status_text = str(pick(game, "status", "gameStatus", "status.name") or "")
        played = bool(pick(game, "played", "isPlayed", "finished"))
        if played or re.search(r"final|finished|played", status_text, re.I):
            state, status = "final", "Final"
        elif re.search(r"live|playing|in progress", status_text, re.I):
            state, status = "live", "Live"
        else:
            state, status = "scheduled", "Scheduled"
        games.append({
            "eventId": "euroleague-" + str(pick(game, "gameCode", "id") or len(games) + 1),
            "date": str(date),
            "displayTime": dt.strftime("%b %d · Final") if state == "final" else dt.strftime("%b %d · %H:%M"),
            "away": str(road),
            "home": str(local),
            "awayScore": str(road_score if road_score is not None else "—"),
            "homeScore": str(local_score if local_score is not None else "—"),
            "status": status,
            "state": state,
            "sourceName": "EuroLeague Official API",
            "sourceUrl": url
        })
    if not games:
        raise RuntimeError("No usable EuroLeague games returned")
    return {
        "league": "EuroLeague",
        "sourceName": "EuroLeague Official API",
        "sourceUrl": url,
        "note": "Automatically refreshed from the official EuroLeague competition feed.",
        "games": games
    }

NPB_TEAMS = [
    "Hanshin Tigers", "Tokyo Yakult Swallows", "Chunichi Dragons",
    "Yokohama DeNA BayStars", "Yomiuri Giants", "Hiroshima Toyo Carp",
    "Tohoku Rakuten Golden Eagles", "Hokkaido Nippon-Ham Fighters",
    "Orix Buffaloes", "Chiba Lotte Marines", "Saitama Seibu Lions",
    "Fukuoka SoftBank Hawks"
]

def npb():
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)
    games = []
    for offset in (-1, 0, 1, 2):
        day = (now + timedelta(days=offset)).date()
        url = "https://npb.jp/bis/eng/2026/games/gm" + day.strftime("%Y%m%d") + ".html"
        try:
            soup = BeautifulSoup(fetch(url), "html.parser")
        except Exception:
            continue
        for row in soup.find_all("tr"):
            text = " ".join(row.stripped_strings)
            found = [team for team in NPB_TEAMS if team.lower() in text.lower()]
            if len(found) < 2:
                continue
            tm = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
            hour, minute = (int(tm.group(1)), int(tm.group(2))) if tm else (12, 0)
            dt = datetime(day.year, day.month, day.day, hour, minute, tzinfo=jst)
            score = re.search(r"\b(\d{1,2})\s*[-–]\s*(\d{1,2})\b", text)
            state = "final" if score else "scheduled"
            games.append({
                "eventId": "npb-" + day.strftime("%Y%m%d") + "-" + str(len(games) + 1),
                "date": dt.isoformat(),
                "displayTime": dt.strftime("%b %d · Final") if state == "final" else dt.strftime("%b %d · %I:%M %p").replace(" 0", " "),
                "away": found[0], "home": found[1],
                "awayScore": score.group(1) if score else "—",
                "homeScore": score.group(2) if score else "—",
                "status": "Final" if state == "final" else "Scheduled",
                "state": state,
                "sourceName": "NPB",
                "sourceUrl": url
            })
    if not games:
        raise RuntimeError("No NPB rows parsed")
    return {
        "league": "NPB", "sourceName": "NPB",
        "sourceUrl": "https://npb.jp/bis/eng/2026/games/",
        "note": "Automatically refreshed from official NPB daily pages.",
        "games": games
    }

KBO_TEAMS = ["KIA Tigers","Samsung Lions","LG Twins","Doosan Bears","KT Wiz","SSG Landers","Lotte Giants","Hanwha Eagles","NC Dinos","Kiwoom Heroes"]

def kbo():
    url = "https://eng.koreabaseball.com/Schedule/DailySchedule.aspx"
    soup = BeautifulSoup(fetch(url), "html.parser")
    text_date = datetime.now(timezone(timedelta(hours=9))).date()
    games = []
    for row in soup.find_all("tr"):
        text = " ".join(row.stripped_strings)
        found = [team for team in KBO_TEAMS if team.lower() in text.lower()]
        if len(found) < 2:
            continue
        tm = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
        hour, minute = (int(tm.group(1)), int(tm.group(2))) if tm else (18, 30)
        dt = datetime(text_date.year, text_date.month, text_date.day, hour, minute, tzinfo=timezone(timedelta(hours=9)))
        score = re.search(r"\b(\d{1,2})\s*[-–:]\s*(\d{1,2})\b", text)
        state = "final" if score else "scheduled"
        games.append({
            "eventId": "kbo-" + text_date.strftime("%Y%m%d") + "-" + str(len(games) + 1),
            "date": dt.isoformat(),
            "displayTime": dt.strftime("%b %d · Final") if state == "final" else dt.strftime("%b %d · %I:%M %p").replace(" 0", " "),
            "away": found[0], "home": found[1],
            "awayScore": score.group(1) if score else "—",
            "homeScore": score.group(2) if score else "—",
            "status": "Final" if state == "final" else "Scheduled",
            "state": state,
            "sourceName": "KBO League",
            "sourceUrl": url
        })
    if not games:
        raise RuntimeError("No KBO rows parsed")
    return {
        "league": "KBO League", "sourceName": "KBO League",
        "sourceUrl": url,
        "note": "Automatically refreshed from the official KBO daily schedule page.",
        "games": games
    }

def boxing_org(org):
    data = json.loads((ROOT / "boxing-data.json").read_text("utf-8"))
    fights = json.loads((ROOT / "boxing-fights-data.json").read_text("utf-8"))
    rx = re.compile(r"^" + re.escape(org) + r"\b", re.I)
    stamp = data.get("updated_at") or datetime.now(timezone.utc).isoformat()
    titled = set()
    holders = []
    for fighter in data.get("fighters", []):
        titles = [t.get("name", "") for t in fighter.get("titles", []) if rx.search(str(t.get("name", "")))]
        if not titles:
            continue
        titled.add(str(fighter.get("name", "")).lower())
        stats = fighter.get("stats") or {}
        division = (fighter.get("division") or {}).get("name", "")
        for title in titles:
            holders.append({
                "eventId": org.lower() + "-holder-" + re.sub(r"[^a-z0-9]+", "-", str(fighter.get("id") or fighter.get("name", "")).lower()).strip("-"),
                "date": stamp, "displayTime": "Current",
                "title": str(fighter.get("name", "")) + " — " + title,
                "location": ((division + " · ") if division else "") + "Record " + str(stats.get("wins", "—")) + "-" + str(stats.get("losses", "—")) + "-" + str(stats.get("draws", "—")),
                "status": "Current titleholder", "state": "info",
                "eventOnly": True, "dataType": "titleholder",
                "sourceName": "IMG Boxing Data", "sourceUrl": "/boxing/"
            })
    bouts = []
    for index, fight in enumerate(fights.get("fights", [])):
        f1 = str(((fight.get("fighters") or {}).get("fighter_1") or {}).get("name", "")).lower()
        f2 = str(((fight.get("fighters") or {}).get("fighter_2") or {}).get("name", "")).lower()
        if f1 not in titled and f2 not in titled:
            continue
        raw = str(fight.get("status", "NOT_STARTED")).upper()
        state = "final" if raw == "FINISHED" else ("live" if raw == "LIVE" else "scheduled")
        event = fight.get("event") or {}
        bouts.append({
            "eventId": org.lower() + "-bout-" + str(fight.get("id") or index),
            "date": fight.get("date"), "displayTime": fight.get("displayTime") or "",
            "title": "Related bout — " + str(fight.get("title", "")),
            "location": " · ".join(x for x in [event.get("venue"), event.get("location")] if x),
            "status": "Final" if state == "final" else ("Live" if state == "live" else "Scheduled"),
            "state": state, "eventOnly": True, "dataType": "relatedBout",
            "sourceName": "IMG Boxing Data", "sourceUrl": "/boxing/"
        })
    return {
        "league": org, "sourceName": "IMG Boxing Data", "sourceUrl": "/boxing/",
        "note": org + " titleholders come from verified title fields in the IMG boxing database; related bouts require a currently titled fighter.",
        "games": bouts[:20] + holders
    }

def main():
    data = load()
    leagues = data.setdefault("leagues", {})
    jobs = [("euroleague", euroleague), ("npb", npb), ("kbo", kbo)]
    for key, builder in jobs:
        try:
            result = builder()
            if result.get("games"):
                leagues[key] = result
            print("updated", key, len(result.get("games", [])))
        except Exception as ex:
            print("preserved", key, type(ex).__name__, str(ex)[:160])
    for org in ("WBC", "WBA", "IBF", "WBO"):
        try:
            result = boxing_org(org)
            if result.get("games"):
                leagues[org.lower()] = result
            print("updated", org.lower(), len(result.get("games", [])))
        except Exception as ex:
            print("preserved", org.lower(), type(ex).__name__, str(ex)[:160])
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    data["source"] = "Official and verified public sports sources"
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")

if __name__ == "__main__":
    main()
