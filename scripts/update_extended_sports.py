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


def wta_live_scores():
    """Clean WTA live-score feed. Never use tournament-level 'In Progress' as a match."""
    official_scores = "https://www.wtatennis.com/scores/"
    browser_headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Mobile Safari/537.36",
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.sofascore.com/",
        "Origin": "https://www.sofascore.com",
    }

    def fetch_json_headers(url, headers):
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))

    def score_text(score):
        if not isinstance(score, dict):
            return "—"
        sets = []
        for n in range(1, 6):
            value = score.get(f"period{n}")
            if value not in (None, ""):
                sets.append(str(value))
        point = score.get("point")
        current = score.get("current")
        if point not in (None, ""):
            return (" ".join(sets) + " · " if sets else "") + str(point)
        if sets:
            return " ".join(sets)
        return str(current) if current not in (None, "") else "—"

    def parse_sofa(payload):
        games = []
        for row in (payload.get("events", []) if isinstance(payload, dict) else []):
            tournament = row.get("tournament") or {}
            category = tournament.get("category") or {}
            slug = str(category.get("slug") or category.get("name") or "").lower()
            name_blob = " ".join([
                str(tournament.get("name") or ""),
                str((tournament.get("uniqueTournament") or {}).get("name") or ""),
                slug,
            ]).lower()
            if "wta" not in name_blob and slug not in {"women", "wta"}:
                continue
            status_obj = row.get("status") or {}
            if str(status_obj.get("type") or "").lower() not in {"inprogress", "live"}:
                continue
            home = row.get("homeTeam") or {}
            away = row.get("awayTeam") or {}
            home_name = str(home.get("name") or home.get("shortName") or "").strip()
            away_name = str(away.get("name") or away.get("shortName") or "").strip()
            if not home_name or not away_name:
                continue
            unique = tournament.get("uniqueTournament") or {}
            tournament_name = str(unique.get("name") or tournament.get("name") or "WTA")
            round_name = str((row.get("roundInfo") or {}).get("name") or "").strip()
            status_desc = str(status_obj.get("description") or "Live").strip()
            start_ts = row.get("startTimestamp")
            date = datetime.fromtimestamp(start_ts, timezone.utc).isoformat() if start_ts else ""
            games.append({
                "eventId": "wta-live-" + str(row.get("id") or row.get("customId") or len(games) + 1),
                "date": date,
                "displayTime": tournament_name,
                "away": away_name,
                "home": home_name,
                "awayScore": score_text(row.get("awayScore")),
                "homeScore": score_text(row.get("homeScore")),
                "status": " · ".join(x for x in [status_desc, round_name] if x) or "Live",
                "state": "live",
                "eventOnly": False,
                "title": tournament_name,
                "sourceName": "Live tennis score feed",
                "sourceUrl": official_scores,
                "verificationSource": "WTA Official Scores",
                "verificationUrl": official_scores,
            })
        return games

    def parse_espn(payload):
        games = []
        for event in (payload.get("events", []) if isinstance(payload, dict) else []):
            comps = event.get("competitions") or []
            for ci, comp in enumerate(comps):
                competitors = comp.get("competitors") or []
                if len(competitors) < 2:
                    continue
                def pname(x):
                    athlete = x.get("athlete") or {}
                    team = x.get("team") or {}
                    return str(athlete.get("displayName") or athlete.get("shortDisplayName") or team.get("displayName") or x.get("displayName") or "").strip()
                a, b = competitors[0], competitors[1]
                an, bn = pname(a), pname(b)
                if not an or not bn:
                    continue
                st = (comp.get("status") or event.get("status") or {}).get("type") or {}
                state_raw = str(st.get("state") or "").lower()
                if state_raw != "in":
                    continue
                def escore(x):
                    lines = x.get("linescores") or []
                    vals = []
                    for ln in lines:
                        if isinstance(ln, dict):
                            v = ln.get("displayValue", ln.get("value"))
                        else:
                            v = ln
                        if v not in (None, ""):
                            vals.append(str(v))
                    score = x.get("score")
                    if isinstance(score, dict):
                        score = score.get("displayValue", score.get("value"))
                    point = x.get("gameScore") or x.get("point")
                    if point not in (None, ""):
                        return (" ".join(vals) + " · " if vals else "") + str(point)
                    if vals:
                        return " ".join(vals)
                    return str(score) if score not in (None, "") else "—"
                status = str(st.get("shortDetail") or st.get("detail") or st.get("description") or "Live")
                games.append({
                    "eventId": "wta-espn-" + str(comp.get("id") or event.get("id") or ci),
                    "date": comp.get("date") or event.get("date") or "",
                    "displayTime": event.get("name") or event.get("shortName") or "WTA",
                    "away": an,
                    "home": bn,
                    "awayScore": escore(a),
                    "homeScore": escore(b),
                    "status": status,
                    "state": "live",
                    "eventOnly": False,
                    "title": event.get("name") or "WTA",
                    "sourceName": "ESPN WTA live scoreboard",
                    "sourceUrl": official_scores,
                    "verificationSource": "WTA Official Scores",
                    "verificationUrl": official_scores,
                })
        return games

    attempts = [
        ("sofascore", "https://api.sofascore.com/api/v1/sport/tennis/events/live", "sofa"),
        ("espn-site", "https://site.api.espn.com/apis/site/v2/sports/tennis/wta/scoreboard", "espn"),
        ("espn-cdn", "https://cdn.espn.com/core/tennis/wta/scoreboard?xhr=1", "espn"),
    ]
    games = []
    errors = []
    for label, url, parser in attempts:
        try:
            payload = fetch_json_headers(url, browser_headers if parser == "sofa" else {"User-Agent": browser_headers["User-Agent"], "Accept": "application/json,*/*"})
            parsed = parse_sofa(payload) if parser == "sofa" else parse_espn(payload)
            print("wta-source", label, "live-matches", len(parsed))
            if parsed:
                games = parsed
                break
        except Exception as ex:
            errors.append(f"{label}:{type(ex).__name__}:{str(ex)[:80]}")
            print("wta-source", label, "error", type(ex).__name__, str(ex)[:120])

    if not games:
        raise RuntimeError("No live WTA matches from clean sources; " + " | ".join(errors))

    # Append only genuinely scheduled future tournaments from the static WTA layer.
    try:
        base = json.loads((ROOT / "special-sports-data.json").read_text("utf-8"))
        base_games = ((base.get("leagues") or {}).get("wta") or {}).get("games") or []
        for game in base_games:
            if game.get("state") == "scheduled":
                games.append(game)
    except Exception:
        pass

    return {
        "league": "WTA Tour",
        "sourceName": "WTA Live Scores",
        "sourceUrl": official_scores,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "note": "Clean WTA feed: live player-v-player matches only; future tournaments remain schedule-only.",
        "games": games,
    }

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

def boxing_weight_class(title):
    text = str(title or "").lower()
    order = [
        ("Heavyweight", ["heavyweight"]),
        ("Bridgerweight", ["bridgerweight"]),
        ("Cruiserweight", ["cruiserweight"]),
        ("Light Heavyweight", ["light heavyweight", "light-heavyweight"]),
        ("Super Middleweight", ["super middleweight", "super-middleweight"]),
        ("Middleweight", ["middleweight"]),
        ("Super Welterweight", ["super welterweight", "junior middleweight", "jr middleweight"]),
        ("Welterweight", ["welterweight"]),
        ("Super Lightweight", ["super lightweight", "junior welterweight", "jr welterweight"]),
        ("Lightweight", ["lightweight"]),
        ("Super Featherweight", ["super featherweight", "junior lightweight", "jr lightweight"]),
        ("Featherweight", ["featherweight"]),
        ("Super Bantamweight", ["super bantamweight", "junior featherweight", "jr featherweight"]),
        ("Bantamweight", ["bantamweight"]),
        ("Super Flyweight", ["super flyweight", "junior bantamweight", "jr bantamweight"]),
        ("Flyweight", ["flyweight"]),
        ("Junior Flyweight", ["junior flyweight", "light flyweight", "jr flyweight"]),
        ("Minimumweight", ["minimumweight", "strawweight"])
    ]
    best = ("Other", 999, -1)
    for index, (label, aliases) in enumerate(order):
        for alias in aliases:
            if alias in text and len(alias) > best[2]:
                best = (label, index, len(alias))
    return best[0], best[1]

def boxing_org(org):
    data = json.loads((ROOT / "boxing-data.json").read_text("utf-8"))
    fights = json.loads((ROOT / "boxing-fights-data.json").read_text("utf-8"))
    ring_mode = org == "RING"
    display_org = "THE RING" if ring_mode else org
    key_org = "ring" if ring_mode else org.lower()
    rx = re.compile(r"^The Ring\b", re.I) if ring_mode else re.compile(r"^" + re.escape(org) + r"\b", re.I)
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
            weight_class, weight_order = boxing_weight_class(title)
            holders.append({
                "eventId": key_org + "-holder-" + re.sub(r"[^a-z0-9]+", "-", str(fighter.get("id") or fighter.get("name", "")).lower()).strip("-"),
                "date": stamp, "displayTime": "Current",
                "title": str(fighter.get("name", "")) + " — " + title,
                "location": ((division + " · ") if division else "") + "Record " + str(stats.get("wins", "—")) + "-" + str(stats.get("losses", "—")) + "-" + str(stats.get("draws", "—")),
                "status": "Current titleholder", "state": "info",
                "eventOnly": True, "dataType": "titleholder",
                "weightClass": weight_class, "weightOrder": weight_order,
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
            "eventId": key_org + "-bout-" + str(fight.get("id") or index),
            "date": fight.get("date"), "displayTime": fight.get("displayTime") or "",
            "title": "Related bout — " + str(fight.get("title", "")),
            "location": " · ".join(x for x in [event.get("venue"), event.get("location")] if x),
            "status": "Final" if state == "final" else ("Live" if state == "live" else "Scheduled"),
            "state": state, "eventOnly": True, "dataType": "relatedBout",
            "sourceName": "IMG Boxing Data", "sourceUrl": "/boxing/"
        })
    return {
        "league": display_org, "sourceName": "The Ring" if ring_mode else "IMG Boxing Data",
        "sourceUrl": "https://www.ringmagazine.com/en/champions/ring/Men" if ring_mode else "/boxing/",
        "note": display_org + " titleholders come from verified title fields in the IMG boxing database; related bouts require a currently titled fighter.",
        "games": bouts[:20] + holders
    }

def main():
    data = load()
    leagues = data.setdefault("leagues", {})
    jobs = [("wta", wta_live_scores), ("euroleague", euroleague), ("npb", npb), ("kbo", kbo)]
    for key, builder in jobs:
        try:
            result = builder()
            if result.get("games"):
                leagues[key] = result
            print("updated", key, len(result.get("games", [])))
        except Exception as ex:
            print("preserved", key, type(ex).__name__, str(ex)[:160])
    for org in ("WBC", "WBA", "IBF", "WBO", "RING"):
        try:
            result = boxing_org(org)
            if result.get("games"):
                leagues["ring" if org == "RING" else org.lower()] = result
            print("updated", "ring" if org == "RING" else org.lower(), len(result.get("games", [])))
        except Exception as ex:
            print("preserved", "ring" if org == "RING" else org.lower(), type(ex).__name__, str(ex)[:160])
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    data["source"] = "Official and verified public sports sources"
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")

if __name__ == "__main__":
    main()
