#!/usr/bin/env python3
import json
import io
import html as html_module
import re
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from bs4 import BeautifulSoup
from pypdf import PdfReader

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


def wta_calendar_schedule():
    """Scrape the official WTA 2026 calendar PDF for current/upcoming Tour events."""
    calendar_url = "https://wtafiles.wtatennis.com/pdf/calendar/calendar.pdf"
    req = urllib.request.Request(
        calendar_url,
        headers={"User-Agent": UA, "Accept": "application/pdf,*/*"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        pdf_bytes = r.read()

    reader = PdfReader(io.BytesIO(pdf_bytes))
    if not reader.pages:
        raise RuntimeError("WTA calendar PDF has no pages")

    # Page 1 is the main WTA Tour calendar. Page 2 is WTA 125.
    text = reader.pages[0].extract_text() or ""
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]

    blocks = []
    current = None
    week_re = re.compile(r"^(\d+(?:\s*&\s*\d+)?)\s+(\d{1,2}-[A-Z]{3})\s*(.*)$")
    for line in lines:
        m = week_re.match(line)
        if m:
            if current:
                blocks.append(current)
            current = {"week": m.group(1), "date": m.group(2), "text": m.group(3).strip()}
        elif current:
            current["text"] += " " + line
    if current:
        blocks.append(current)

    now = datetime.now(timezone.utc)
    games = []
    seen = set()
    event_re = re.compile(r"([^|]+?)\s*\|\s*([^|]+?)\s*-\s*((?:I\s*)?[HCG])(?=\s|$)")

    # Exact dates currently published on WTA's tournament pages.
    exact_dates = {
        "Singapore Tennis Open": ("2026-09-21", "2026-09-27"),
        "Korea Open": ("2026-09-21", "2026-09-27"),
        "China Open": ("2026-09-30", "2026-10-11"),
        "Wuhan Open": ("2026-10-12", "2026-10-18"),
        "WTA Finals Indian Wells": ("2026-11-08", "2026-11-15"),
    }
    levels = {
        "Singapore Tennis Open": "WTA 500",
        "Korea Open": "WTA 250",
        "China Open": "WTA 1000",
        "Wuhan Open": "WTA 1000",
        "WTA Finals Indian Wells": "WTA Finals",
    }

    for block in blocks:
        try:
            week_start = datetime.strptime(block["date"] + "-2026", "%d-%b-%Y").replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if week_start < now - timedelta(days=8):
            continue

        blob = block["text"]
        blob = re.sub(r"\bBJK Cup Finals\b", " ", blob, flags=re.I)
        blob = re.sub(r"\bBJK Cup Playoffs\b", " ", blob, flags=re.I)
        # The PDF extraction splits Hong Kong's tournament name and location
        # across lines without a pipe, so normalize that week before parsing.
        if block["date"] == "2-NOV":
            blob = re.sub(
                r"Chennai Open\s*\|\s*Chennai\s*-\s*H\*?\s*Prudential Hong Kong Tennis Open\s+Hong Kong\s*-\s*H",
                "Chennai Open | Chennai - H Prudential Hong Kong Tennis Open | Hong Kong - H",
                blob,
                flags=re.I,
            )

        for match in event_re.finditer(blob):
            name = re.sub(r"\s+", " ", match.group(1)).strip(" -")
            location = re.sub(r"\s+", " ", match.group(2)).strip(" -")
            surface_code = re.sub(r"\s+", " ", match.group(3)).strip().upper()
            if not name or not location:
                continue

            # Remove week/date residue if the PDF extractor attached it to a name.
            name = re.sub(r"^\d+(?:\s*&\s*\d+)?\s+\d{1,2}-[A-Z]{3}\s+", "", name).strip()
            if not name:
                continue

            key = name.lower()
            if key in seen:
                continue
            seen.add(key)

            start_date = week_start.date().isoformat()
            end_date = (week_start + timedelta(days=6)).date().isoformat()
            for official_name, pair in exact_dates.items():
                if official_name.lower() == key:
                    start_date, end_date = pair
                    break

            start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
            end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
            if end_dt < now - timedelta(days=1):
                continue

            surface = {
                "H": "Hard",
                "I H": "Indoor Hard",
                "C": "Clay",
                "I C": "Indoor Clay",
                "G": "Grass",
            }.get(surface_code, surface_code)

            if name in exact_dates:
                start_label = start_dt.strftime("%b %-d")
                end_label = end_dt.strftime("%b %-d")
                display = f"{start_label}–{end_label}"
            else:
                display = "Week of " + week_start.strftime("%b %-d")

            games.append({
                "eventId": "wta-calendar-" + re.sub(r"[^a-z0-9]+", "-", key).strip("-"),
                "date": start_dt.isoformat(),
                "endDate": end_dt.isoformat(),
                "displayTime": display,
                "title": name,
                "location": location,
                "status": "Tournament in progress" if start_dt <= now <= end_dt + timedelta(days=1) else "Scheduled",
                "state": "scheduled",
                "eventOnly": True,
                "level": levels.get(name, ""),
                "surface": surface,
                "sourceName": "WTA Official Calendar",
                "sourceUrl": calendar_url,
            })

    if not games:
        raise RuntimeError("WTA official calendar PDF produced no current/upcoming Tour events")

    games.sort(key=lambda g: g.get("date") or "")
    return {
        "league": "WTA Tour",
        "sourceName": "WTA Official Calendar",
        "sourceUrl": calendar_url,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "note": "Current and upcoming WTA Tour tournaments scraped automatically from the official WTA calendar PDF.",
        "games": games,
    }


def wta_live_scores():
    """Scrape WTA's official score pages for live player-v-player matches."""
    official_scores = "https://www.wtatennis.com/scores/"
    tournaments = [
        ("Singapore Tennis Open", "https://www.wtatennis.com/tournaments/1152/singapore/2026/scores"),
        ("Korea Open", "https://www.wtatennis.com/tournaments/1024/seoul/2026/scores"),
        ("Turk Telekom Ankara Open", "https://www.wtatennis.com/tournaments/1178/ankara-125/2026/scores"),
        ("Delta Motors Tolentino Open", "https://www.wtatennis.com/tournaments/1133/tolentino-125/2026/scores"),
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Mobile Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def fetch_text(url):
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", errors="replace")

    def walk(value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from walk(child)
        elif isinstance(value, list):
            for child in value:
                yield from walk(child)

    def scalar(d, keys):
        lower = {str(k).lower(): v for k, v in d.items()}
        for key in keys:
            v = lower.get(key.lower())
            if isinstance(v, (str, int, float)) and str(v).strip():
                return str(v).strip()
        return ""

    def person_name(value):
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, dict):
            return scalar(value, ["displayName","fullName","playerName","name","shortName"])
        return ""

    def score_parts(value):
        sets = []
        point = ""
        if isinstance(value, dict):
            for key in ("set1","set2","set3","set4","set5","period1","period2","period3","period4","period5"):
                if key in value and value[key] not in (None, ""):
                    sets.append(str(value[key]))
            for key in ("point","gamePoint","gameScore","currentPoint"):
                if key in value and value[key] not in (None, ""):
                    point = str(value[key])
                    break
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    v = scalar(item, ["displayValue","value","score","games"])
                elif isinstance(item, (str, int, float)):
                    v = str(item)
                else:
                    v = ""
                if v:
                    sets.append(v)
        return {"sets": sets[:5], "point": point}

    def score_value(value):
        parts = score_parts(value)
        text = " ".join(parts["sets"])
        if parts["point"]:
            return (text + " · " if text else "") + parts["point"]
        if text:
            return text
        if isinstance(value, (str, int, float)):
            return str(value)
        if isinstance(value, dict):
            return scalar(value, ["displayValue","value","score"]) or "—"
        return "—"

    def match_from_dict(d, tournament):
        status = scalar(d, ["matchState","state","status","matchStatus","statusText","matchStatusText"])
        low = status.lower()
        if not re.search(r"live|progress|playing|medical|set|break|suspended", low):
            return None

        a = person_name(d.get("playerA") or d.get("entrantA") or d.get("competitorA") or d.get("participantA") or d.get("teamA"))
        b = person_name(d.get("playerB") or d.get("entrantB") or d.get("competitorB") or d.get("participantB") or d.get("teamB"))
        if not a or not b:
            players=d.get("players") or d.get("competitors") or d.get("participants")
            if isinstance(players,list) and len(players)>=2:
                a,b=person_name(players[0]),person_name(players[1])
        if not a or not b or a==b:
            return None

        raw_a = d.get("scoreA") or d.get("playerAScore") or d.get("homeScore") or d.get("score1")
        raw_b = d.get("scoreB") or d.get("playerBScore") or d.get("awayScore") or d.get("score2")
        parts_a = score_parts(raw_a)
        parts_b = score_parts(raw_b)
        sa = score_value(raw_a)
        sb = score_value(raw_b)
        round_name=scalar(d,["round","roundName","drawLevelType"])
        court=scalar(d,["court","courtName"])
        mid=scalar(d,["matchId","id","eventId"]) or re.sub(r"[^a-z0-9]+","-",f"{tournament}-{a}-{b}".lower()).strip("-")
        return {
            "eventId":"wta-scrape-"+mid,
            "date":datetime.now(timezone.utc).isoformat(),
            "displayTime":tournament,
            "away":a,"home":b,
            "awayScore":sa,"homeScore":sb,
            "awaySets":parts_a["sets"],"homeSets":parts_b["sets"],
            "awayPoint":parts_a["point"],"homePoint":parts_b["point"],
            "status":" · ".join(x for x in [status or "Live",round_name,court] if x),
            "state":"live","eventOnly":False,"title":tournament,
            "sourceName":"WTA Official Scores","sourceUrl":official_scores,
            "verificationSource":"WTA Official Scores","verificationUrl":official_scores,
        }

    games=[]
    seen=set()
    fetched_pages=0
    for tournament,url in tournaments:
        try:
            html=fetch_text(url)
        except Exception as ex:
            print("wta-scrape",tournament,"fetch-error",type(ex).__name__,str(ex)[:100])
            continue

        fetched_pages+=1
        payloads=[]
        for m in re.finditer(r'<script[^>]*type=["\\\']application/json["\\\'][^>]*>(.*?)</script>',html,re.I|re.S):
            raw=html_module.unescape(m.group(1)).strip()
            try: payloads.append(json.loads(raw))
            except Exception: pass
        next_m=re.search(r'<script[^>]*id=["\\\']__NEXT_DATA__["\\\'][^>]*>(.*?)</script>',html,re.I|re.S)
        if next_m:
            try: payloads.append(json.loads(html_module.unescape(next_m.group(1))))
            except Exception: pass

        found=0
        for payload in payloads:
            for d in walk(payload):
                game=match_from_dict(d,tournament)
                if not game: continue
                key=(game["away"].lower(),game["home"].lower())
                if key in seen: continue
                seen.add(key); games.append(game); found+=1
        print("wta-scrape",tournament,"json-blocks",len(payloads),"live-matches",found)

    if not games and fetched_pages == 0:
        raise RuntimeError("WTA live pages were unavailable")

    return {
        "league":"WTA Tour",
        "sourceName":"WTA Official Scores",
        "sourceUrl":official_scores,
        "updatedAt":datetime.now(timezone.utc).isoformat(),
        "note":"Live WTA scores scraped from official WTA score pages.",
        "games":games,
    }


def premier_league_games():
    """Refresh verified EPL recent/upcoming fixtures from ESPN's English top-flight feed."""
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=10)).strftime("%Y%m%d")
    end = (now + timedelta(days=21)).strftime("%Y%m%d")
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?dates={start}-{end}"
    payload = fetch_json(url)
    events = payload.get("events", []) if isinstance(payload, dict) else []
    games = []
    for event in events:
        comps = event.get("competitions") or []
        comp = comps[0] if comps else {}
        competitors = comp.get("competitors") or []
        home = next((x for x in competitors if x.get("homeAway") == "home"), competitors[0] if competitors else {})
        away = next((x for x in competitors if x.get("homeAway") == "away"), competitors[1] if len(competitors) > 1 else {})
        home_team = home.get("team") or {}
        away_team = away.get("team") or {}
        home_name = home_team.get("displayName") or home_team.get("shortDisplayName") or "TBD"
        away_name = away_team.get("displayName") or away_team.get("shortDisplayName") or "TBD"
        if home_name == "TBD" and away_name == "TBD":
            continue

        status_type = ((comp.get("status") or {}).get("type") or {})
        raw_state = status_type.get("state") or "pre"
        state = "live" if raw_state == "in" else ("final" if raw_state == "post" else "scheduled")
        status = status_type.get("shortDetail") or status_type.get("detail") or status_type.get("description") or ("Final" if state == "final" else "Scheduled")
        date = comp.get("date") or event.get("date")
        home_score = home.get("score")
        away_score = away.get("score")
        if state == "scheduled":
            home_score = "—"
            away_score = "—"

        games.append({
            "eventId": str(event.get("id") or comp.get("id") or ""),
            "date": date,
            "displayTime": status,
            "away": away_name,
            "home": home_name,
            "awayLogo": ((away_team.get("logos") or [{}])[0] or {}).get("href", ""),
            "homeLogo": ((home_team.get("logos") or [{}])[0] or {}).get("href", ""),
            "awayScore": str(away_score if away_score not in (None, "") else "—"),
            "homeScore": str(home_score if home_score not in (None, "") else "—"),
            "status": status,
            "state": state,
            "sourceName": "ESPN EPL feed",
            "sourceUrl": url
        })
    if not games:
        raise RuntimeError("No verified EPL games returned")
    games.sort(key=lambda g: g.get("date") or "")

    standings_url = "https://site.api.espn.com/apis/v2/sports/soccer/eng.1/standings?season=2026"
    standings = []
    try:
        table = fetch_json(standings_url)
        children = table.get("children", []) if isinstance(table, dict) else []
        entries = []
        for child in children:
            entries.extend(((child.get("standings") or {}).get("entries") or []))
        for entry in entries:
            team = entry.get("team") or {}
            stats = {str(x.get("name") or x.get("abbreviation") or ""): x for x in (entry.get("stats") or [])}
            def sval(*names):
                for name in names:
                    item = stats.get(name)
                    if item:
                        return item.get("displayValue") if item.get("displayValue") not in (None, "") else item.get("value")
                return ""
            standings.append({
                "rank": sval("rank", "Rank"),
                "team": team.get("displayName") or team.get("shortDisplayName") or team.get("name") or "",
                "played": sval("gamesPlayed", "GP"),
                "wins": sval("wins", "W"),
                "draws": sval("ties", "draws", "D"),
                "losses": sval("losses", "L"),
                "goalDiff": sval("pointDifferential", "goalDifference", "GD"),
                "points": sval("points", "PTS")
            })
        standings = [x for x in standings if x["team"]]
    except Exception as ex:
        print("epl-standings", type(ex).__name__, str(ex)[:120])

    return {
        "league": "EPL",
        "season": "2026–27",
        "sourceName": "ESPN EPL feed",
        "sourceUrl": url,
        "standingsSourceUrl": standings_url,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "note": "Verified EPL-only rolling window: recent results plus upcoming fixtures.",
        "standings": standings,
        "games": games
    }


def fiba_games():
    """Refresh FIBA games from official FIBA competition pages."""
    hub_url = "https://www.fiba.basketball/en/games"
    event_urls = [
        ("FIBA Intercontinental Cup 2026", "https://www.fiba.basketball/en/events/fiba-intercontinental-cup-2026"),
        ("FIBA Europe Cup 2026-27", "https://www.fiba.basketball/en/events/fiba-europe-cup-2026-27"),
        ("EuroCup Women 2026-27", "https://www.fiba.basketball/en/events/eurocup-women-2026-27"),
        ("EuroLeague Women 2026-27", "https://www.fiba.basketball/en/events/euroleague-women-2026-27"),
        ("FIBA West Asia Super League Final 8", "https://www.fiba.basketball/en/events/fiba-wasl-final-8-2025-26"),
    ]

    now = datetime.now(timezone.utc)
    games = []
    seen = set()
    fetched = 0

    month_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
    }

    def parse_card(event_name, event_url, text, context):
        text = re.sub(r"\s+", " ", text).strip()
        context = re.sub(r"\s+", " ", context).strip()
        # FIBA cards repeat each team's short code, e.g. "VILN VILN 107 RSSB RSSB 89".
        m = re.search(
            r"\b([A-Z0-9]{2,8})\s+\1(?:\s+(\d{1,3}))?\s+([A-Z0-9]{2,8})\s+\3(?:\s+(\d{1,3}))?\b",
            text,
        )
        if not m:
            return None

        away, away_score, home, home_score = m.group(1), m.group(2), m.group(3), m.group(4)
        low = text.lower()
        if "final" in low:
            state, status = "final", "Final"
        elif re.search(r"\blive\b|\bq[1-4]\b|quarter|halftime|overtime|\bot\b|in progress", low):
            state, status = "live", "Live"
        else:
            state, status = "scheduled", "Scheduled"

        dm = re.search(r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s*([A-Za-z]{3,4})\s+(\d{1,2})\b", context, re.I)
        year = now.year
        date_value = now.isoformat()
        display = status
        if dm:
            month = month_map.get(dm.group(1).lower())
            day = int(dm.group(2))
            if month:
                dt = datetime(year, month, day, 0, 0, tzinfo=timezone.utc)
                # Handle year rollover for late-December pages listing January games.
                if dt < now - timedelta(days=120):
                    dt = dt.replace(year=year + 1)
                date_value = dt.isoformat()
                display = dt.strftime("%b %d")
        tm = re.search(r"\b([0-2]?\d:[0-5]\d)\b", context)
        if tm and state == "scheduled":
            display += " · " + tm.group(1)
        elif state == "final":
            display += " · Final"
        elif state == "live":
            display += " · Live"

        phase = text[:m.start()].strip(" ·-")
        event_id = re.sub(r"[^a-z0-9]+", "-", f"{event_name}-{date_value[:10]}-{away}-{home}".lower()).strip("-")
        return {
            "eventId": "fiba-" + event_id,
            "date": date_value,
            "displayTime": display,
            "away": away,
            "home": home,
            "awayScore": away_score or "—",
            "homeScore": home_score or "—",
            "status": status,
            "state": state,
            "title": " · ".join(x for x in [event_name, phase] if x),
            "sourceName": "FIBA Official",
            "sourceUrl": event_url,
            "verificationSource": "FIBA Official",
            "verificationUrl": event_url,
        }

    for event_name, event_url in event_urls:
        try:
            soup = BeautifulSoup(fetch(event_url), "html.parser")
            fetched += 1
        except Exception as ex:
            print("fiba-event", event_name, "fetch-error", type(ex).__name__, str(ex)[:100])
            continue

        found = 0
        for a in soup.find_all("a"):
            text = " ".join(a.stripped_strings)
            if not text:
                continue
            parent = a.parent
            context = " ".join(parent.stripped_strings) if parent else text
            game = parse_card(event_name, event_url, text, context)
            if not game:
                continue
            key = (game["date"][:10], game["away"], game["home"])
            if key in seen:
                continue
            seen.add(key)
            games.append(game)
            found += 1
        print("fiba-event", event_name, "games", found)

    if fetched == 0:
        raise RuntimeError("All FIBA event pages were unavailable")

    # Keep the useful current window; final games remain briefly for post-game viewing.
    floor = now - timedelta(days=7)
    ceiling = now + timedelta(days=35)
    filtered = []
    for game in games:
        dt = parse_iso(game.get("date"))
        if not dt:
            filtered.append(game)
            continue
        dt = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        if floor <= dt <= ceiling:
            filtered.append(game)

    filtered.sort(key=lambda g: g.get("date") or "")
    return {
        "league": "FIBA",
        "sourceName": "FIBA Official",
        "sourceUrl": hub_url,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "note": "Automatically refreshed from official FIBA competition game cards.",
        "games": filtered,
    }

def cba_games():
    """Refresh CBA schedule from the official CBA league website."""
    official_url = "https://www.cbaleague.com/"
    source_urls = [
        official_url,
        "https://r.jina.ai/http://www.cbaleague.com/",
    ]
    teams = [
        "上海久事","浙江浙商证券","深圳马可波罗","北京首钢","广东东阳光","浙江稠州金租",
        "山东高速","山西汾酒","青岛崂山啤酒","辽宁本钢","宁波町渥","广州智都","北京控股",
        "福建晋江文旅","长白山恩都里","新疆广汇能源","南京同曦宙光","天津先行者","江苏肯帝亚","四川锦城"
    ]
    now_cn = datetime.now(timezone(timedelta(hours=8)))

    def parse_text(text):
        lines = [re.sub(r"\\s+", " ", x).strip() for x in str(text).splitlines() if str(x).strip()]
        games, seen = [], set()
        current_date = None
        current_time = None

        def add_game(date_value, time_value, away, home, round_label=""):
            if not date_value or not away or not home or away == home:
                return
            key = (date_value, time_value or "", away, home)
            if key in seen:
                return
            seen.add(key)
            hh, mm = 12, 0
            if time_value and re.fullmatch(r"[0-2]?\\d:[0-5]\\d", time_value):
                hh, mm = map(int, time_value.split(":"))
            dt = datetime.strptime(date_value, "%Y-%m-%d").replace(hour=hh, minute=mm, tzinfo=timezone(timedelta(hours=8)))
            if dt < now_cn - timedelta(days=7) or dt > now_cn + timedelta(days=240):
                return
            games.append({
                "eventId": "cba-" + date_value.replace("-", "") + "-" + str(len(games)+1),
                "date": dt.isoformat(),
                "displayTime": dt.strftime("%b %d · %H:%M"),
                "away": away,
                "home": home,
                "awayScore": "—",
                "homeScore": "—",
                "status": "Scheduled",
                "state": "scheduled",
                "round": round_label,
                "sourceName": "CBA Official",
                "sourceUrl": official_url
            })

        # Pattern 1: round/date/time on one line, followed by the two teams.
        for i, line in enumerate(lines):
            m = re.search(r"(第\\d+轮)?\\s*(20\\d{2}-\\d{2}-\\d{2})\\s+([0-2]?\\d:[0-5]\\d)", line)
            if not m:
                continue
            found = []
            for nxt in lines[i+1:i+10]:
                clean = re.sub(r"^(?:Image|图片)\\s*", "", nxt).strip()
                if clean in teams and clean not in found:
                    found.append(clean)
                if len(found) >= 2:
                    break
            if len(found) >= 2:
                add_game(m.group(2), m.group(3), found[0], found[1], m.group(1) or "")

        # Pattern 2: homepage schedule cards with date and time on separate lines.
        for i, line in enumerate(lines):
            dm = re.fullmatch(r"(20\\d{2}-\\d{2}-\\d{2})", line)
            if dm:
                current_date = dm.group(1)
                current_time = None
                continue
            tm = re.fullmatch(r"([0-2]?\\d:[0-5]\\d)", line)
            if tm:
                current_time = tm.group(1)
                continue
            if line.lower() != "vs" or not current_date:
                continue
            before = []
            after = []
            for prev in reversed(lines[max(0, i-10):i]):
                clean = re.sub(r"^(?:Image|图片)\\s*", "", prev).strip()
                if clean in teams:
                    before.append(clean)
                    break
            for nxt in lines[i+1:i+11]:
                clean = re.sub(r"^(?:Image|图片)\\s*", "", nxt).strip()
                if clean in teams:
                    after.append(clean)
                    break
            if before and after:
                add_game(current_date, current_time, before[0], after[0])

        games.sort(key=lambda g: g["date"])
        return games

    games = []
    used_url = official_url
    last_error = None
    for url in source_urls:
        try:
            raw = fetch(url)
            parsed = parse_text(BeautifulSoup(raw, "html.parser").get_text("\n") if "<html" in raw.lower() else raw)
            if parsed:
                games = parsed
                used_url = url
                break
        except Exception as ex:
            last_error = ex

    if not games:
        raise RuntimeError("No current CBA fixtures parsed from official site" + (": " + str(last_error)[:120] if last_error else ""))

    return {
        "league": "CBA",
        "season": "2026–27",
        "sourceName": "CBA Official",
        "sourceUrl": official_url,
        "retrievalUrl": used_url,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "note": "Automatically refreshed from the official CBA league schedule.",
        "games": games
    }


def wcba_games():
    """Publish verified WCBA season calendar and later replace/extend it with fixtures."""
    url = "https://www.cba.net.cn/wcbasy/index.jhtml"
    try:
        fetch(url)
    except Exception:
        pass

    tz_cn = timezone(timedelta(hours=8))
    milestones = [
        ("wcba-2026-regular-season", "2026-11-14T12:00:00+08:00", "WCBA Regular Season begins", "Nov 14 · Regular season"),
        ("wcba-2027-all-star", "2027-02-27T12:00:00+08:00", "WCBA All-Star Weekend", "Feb 27–28 · All-Star"),
        ("wcba-2027-playoffs", "2027-03-04T12:00:00+08:00", "WCBA Playoffs begin", "Mar 4 · Playoffs"),
    ]
    games = []
    for event_id, date_value, title, display in milestones:
        games.append({
            "eventId": event_id,
            "date": date_value,
            "displayTime": display,
            "title": title,
            "away": "",
            "home": "",
            "awayScore": "—",
            "homeScore": "—",
            "status": "Scheduled",
            "state": "scheduled",
            "eventOnly": True,
            "sourceName": "China Basketball Association / WCBA",
            "sourceUrl": url
        })

    return {
        "league": "WCBA",
        "season": "2026–27",
        "sourceName": "China Basketball Association / WCBA",
        "sourceUrl": url,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "note": "2026–27 WCBA calendar is published: 32-round regular season Nov 14, 2026–Feb 23, 2027; All-Star Feb 27–28; playoffs Mar 4–Apr 9 at the latest. Individual fixtures will populate when officially published.",
        "games": games
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
    jobs = [("soccer", premier_league_games), ("wta", wta_calendar_schedule), ("fiba", fiba_games), ("euroleague", euroleague), ("cba", cba_games), ("wcba", wcba_games), ("npb", npb), ("kbo", kbo)]
    for key, builder in jobs:
        try:
            result = builder()
            if key in ("cba", "wcba") or result.get("games"):
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
