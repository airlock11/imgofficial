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


def fiba_games():
    """Refresh FIBA games from the official FIBA Games & Results page."""
    url = "https://www.fiba.basketball/en/games"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    payloads = []
    for tag in soup.find_all("script"):
        typ = str(tag.get("type") or "").lower()
        sid = str(tag.get("id") or "")
        if typ == "application/json" or sid == "__NEXT_DATA__":
            raw = tag.string or tag.get_text() or ""
            raw = html_module.unescape(raw).strip()
            if not raw:
                continue
            try:
                payloads.append(json.loads(raw))
            except Exception:
                pass

    def walk(value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from walk(child)
        elif isinstance(value, list):
            for child in value:
                yield from walk(child)

    def scalar(obj, names):
        if not isinstance(obj, dict):
            return ""
        lower = {str(k).lower(): v for k, v in obj.items()}
        for name in names:
            v = lower.get(name.lower())
            if isinstance(v, (str, int, float)) and str(v).strip():
                return str(v).strip()
        return ""

    def team_name(value):
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, dict):
            direct = scalar(value, ["name", "displayName", "shortName", "teamName", "officialName", "code"])
            if direct:
                return direct
            for key in ("team", "competitor", "participant"):
                if key in value:
                    found = team_name(value.get(key))
                    if found:
                        return found
        return ""

    def score_value(value):
        if isinstance(value, (str, int, float)):
            return str(value)
        if isinstance(value, dict):
            return scalar(value, ["score", "points", "value", "displayValue", "total"]) or "—"
        return "—"

    now = datetime.now(timezone.utc)
    games = []
    seen = set()

    for payload in payloads:
        for d in walk(payload):
            if not isinstance(d, dict):
                continue

            home_raw = (
                d.get("homeTeam") or d.get("teamHome") or d.get("home") or
                d.get("teamB") or d.get("competitor2")
            )
            away_raw = (
                d.get("awayTeam") or d.get("teamAway") or d.get("away") or
                d.get("teamA") or d.get("competitor1")
            )

            if (not home_raw or not away_raw) and isinstance(d.get("teams"), list) and len(d["teams"]) >= 2:
                away_raw, home_raw = d["teams"][0], d["teams"][1]
            if (not home_raw or not away_raw) and isinstance(d.get("competitors"), list) and len(d["competitors"]) >= 2:
                away_raw, home_raw = d["competitors"][0], d["competitors"][1]
            if (not home_raw or not away_raw) and isinstance(d.get("participants"), list) and len(d["participants"]) >= 2:
                away_raw, home_raw = d["participants"][0], d["participants"][1]

            home = team_name(home_raw)
            away = team_name(away_raw)
            if not home or not away or home == away:
                continue

            raw_date = scalar(d, [
                "gameDateTime", "startDateTime", "startTime", "scheduledAt",
                "dateTime", "utcDate", "date"
            ])
            dt = parse_iso(raw_date)
            if dt:
                dt_utc = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                if not (now - timedelta(days=14) <= dt_utc <= now + timedelta(days=45)):
                    continue
                date_value = dt_utc.isoformat()
            else:
                date_value = raw_date or now.isoformat()

            status_text = scalar(d, [
                "status", "gameStatus", "statusText", "gameStatusText",
                "phase", "state"
            ])
            low = status_text.lower()
            if re.search(r"final|finished|ended|complete", low):
                state, status = "final", "Final"
            elif re.search(r"live|playing|in progress|quarter|q[1-4]|overtime|ot", low):
                state, status = "live", status_text or "Live"
            else:
                state, status = "scheduled", status_text or "Scheduled"

            home_score = score_value(
                d.get("homeScore") or d.get("scoreHome") or
                (home_raw.get("score") if isinstance(home_raw, dict) else None)
            )
            away_score = score_value(
                d.get("awayScore") or d.get("scoreAway") or
                (away_raw.get("score") if isinstance(away_raw, dict) else None)
            )

            event_id = scalar(d, ["id", "gameId", "eventId", "gameCode", "code"])
            if not event_id:
                event_id = re.sub(r"[^a-z0-9]+", "-", f"{date_value}-{away}-{home}".lower()).strip("-")

            title = scalar(d, ["competitionName", "eventName", "tournamentName", "competition", "event"])
            key = (str(event_id), away.lower(), home.lower())
            if key in seen:
                continue
            seen.add(key)

            games.append({
                "eventId": "fiba-" + str(event_id),
                "date": date_value,
                "displayTime": (dt.strftime("%b %d · %H:%M") if dt and state != "final" else ("Final" if state == "final" else status)),
                "away": away,
                "home": home,
                "awayScore": away_score,
                "homeScore": home_score,
                "status": status,
                "state": state,
                "title": title,
                "sourceName": "FIBA Official Games",
                "sourceUrl": url,
                "verificationSource": "FIBA Official Games",
                "verificationUrl": url,
            })

    games.sort(key=lambda g: g.get("date") or "")
    if not payloads:
        raise RuntimeError("FIBA page returned no structured JSON payloads")

    return {
        "league": "FIBA",
        "sourceName": "FIBA Official Games",
        "sourceUrl": url,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "note": "Automatically refreshed from FIBA's official Games & Results page.",
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
    jobs = [("wta", wta_calendar_schedule), ("fiba", fiba_games), ("euroleague", euroleague), ("npb", npb), ("kbo", kbo)]
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
