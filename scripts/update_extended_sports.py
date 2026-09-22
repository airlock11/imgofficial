#!/usr/bin/env python3
import json
import html as html_module
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


def wta_calendar_schedule():
    """Scrape official WTA tournament pages for current and upcoming schedule."""
    official_calendar = "https://www.wtatennis.com/tournaments"
    pages = [
        "https://www.wtatennis.com/tournaments/1152/singapore/2026",
        "https://www.wtatennis.com/tournaments/1024/seoul/2026",
        "https://www.wtatennis.com/tournaments/china-open",
        "https://www.wtatennis.com/tournaments/1075/wuhan/2026/",
        "https://www.wtatennis.com/tournaments/wta-finals",
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; IMG-Sports-Website/1.0; +https://imgofficial.com)",
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def fetch_text(url):
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", errors="replace")

    def clean_text(value):
        return re.sub(r"\\s+", " ", html_module.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()

    def first(pattern, text, flags=re.I|re.S):
        m = re.search(pattern, text, flags)
        return clean_text(m.group(1)) if m else ""

    def parse_date_range(date_text):
        m = re.search(
            r"([A-Z][a-z]{2,8})\\s+(\\d{1,2})\\s*-\\s*(?:([A-Z][a-z]{2,8})\\s+)?(\\d{1,2}),\\s*(2026)",
            date_text or "",
        )
        if not m:
            return "", ""
        sm, sd, em, ed, year = m.groups()
        em = em or sm
        for fmt in ("%b %d %Y", "%B %d %Y"):
            try:
                start = datetime.strptime(f"{sm} {sd} {year}", fmt).replace(tzinfo=timezone.utc)
                end = datetime.strptime(f"{em} {ed} {year}", fmt).replace(tzinfo=timezone.utc)
                return start.isoformat(), end.isoformat()
            except Exception:
                pass
        return "", ""

    def first_int(pattern, text):
        value = first(pattern, text)
        m = re.search(r"\\d+", value or "")
        return int(m.group(0)) if m else ""

    now = datetime.now(timezone.utc)
    games = []
    seen = set()

    for url in pages:
        try:
            html = fetch_text(url)
        except Exception as ex:
            print("wta-calendar fetch-error", url, type(ex).__name__, str(ex)[:100])
            continue

        page_text = clean_text(html)
        title = first(r"<h1[^>]*>(.*?)</h1>", html) or first(r"<title[^>]*>(.*?)</title>", html)
        location = first(r"([A-Z][A-Z .'-]+\\s*•\\s*[A-Z]{3})", page_text)
        level = first(r"(WTA\\s*(?:125|250|500|1000|Finals))", page_text)
        surface = first(r"\\b(Hard|Clay|Grass)\\b", page_text)
        date_text = first(
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\\s+\\d{1,2}\\s*-\\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\\s+)?\\d{1,2},\\s*2026)",
            page_text,
        )
        start_iso, end_iso = parse_date_range(date_text)

        if not title or not start_iso:
            print("wta-calendar parse-miss", url, bool(title), bool(start_iso))
            continue

        start_dt = datetime.fromisoformat(start_iso)
        end_dt = datetime.fromisoformat(end_iso) if end_iso else start_dt
        if end_dt < now - timedelta(days=1):
            continue

        event_id = "wta-calendar-" + re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        if event_id in seen:
            continue
        seen.add(event_id)

        games.append({
            "eventId": event_id,
            "date": start_iso,
            "endDate": end_iso,
            "displayTime": date_text,
            "title": title,
            "location": location.replace(" • ", ", ") if location else "",
            "status": "Tournament in progress" if start_dt <= now <= end_dt + timedelta(days=1) else "Scheduled",
            "state": "scheduled",
            "eventOnly": True,
            "level": level,
            "surface": surface,
            "singlesDraw": first_int(r"Singles Draw\\s*(\\d+)", page_text),
            "doublesDraw": first_int(r"Doubles Draw\\s*(\\d+)", page_text),
            "totalCommitment": first(r"Total \\$ Commitment\\s*(\\$[\\d,]+)", page_text),
            "sourceName": "WTA Official",
            "sourceUrl": url,
        })

    if not games:
        raise RuntimeError("WTA calendar scrape found no current/upcoming tournaments")

    games.sort(key=lambda g: g.get("date") or "")
    return {
        "league": "WTA Tour",
        "sourceName": "WTA Official Calendar",
        "sourceUrl": official_calendar,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "note": "Current and upcoming WTA tournaments scraped from official WTA tournament pages.",
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

    def score_value(value):
        if isinstance(value, (str, int, float)):
            return str(value)
        if isinstance(value, list):
            vals=[score_value(x) for x in value]
            return " ".join(x for x in vals if x and x!="—") or "—"
        if isinstance(value, dict):
            vals=[]
            for key in ("point","current","set1","set2","set3","set4","set5","period1","period2","period3","period4","period5"):
                if key in value and value[key] not in (None,""):
                    vals.append(str(value[key]))
            return " ".join(vals) if vals else scalar(value,["displayValue","value","score"]) or "—"
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

        sa = score_value(d.get("scoreA") or d.get("playerAScore") or d.get("homeScore") or d.get("score1"))
        sb = score_value(d.get("scoreB") or d.get("playerBScore") or d.get("awayScore") or d.get("score2"))
        round_name=scalar(d,["round","roundName","drawLevelType"])
        court=scalar(d,["court","courtName"])
        mid=scalar(d,["matchId","id","eventId"]) or re.sub(r"[^a-z0-9]+","-",f"{tournament}-{a}-{b}".lower()).strip("-")
        return {
            "eventId":"wta-scrape-"+mid,
            "date":datetime.now(timezone.utc).isoformat(),
            "displayTime":tournament,
            "away":a,"home":b,
            "awayScore":sa,"homeScore":sb,
            "status":" · ".join(x for x in [status or "Live",round_name,court] if x),
            "state":"live","eventOnly":False,"title":tournament,
            "sourceName":"WTA Official Scores","sourceUrl":official_scores,
            "verificationSource":"WTA Official Scores","verificationUrl":official_scores,
        }

    games=[]
    seen=set()
    for tournament,url in tournaments:
        try:
            html=fetch_text(url)
        except Exception as ex:
            print("wta-scrape",tournament,"fetch-error",type(ex).__name__,str(ex)[:100])
            continue

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

    if not games:
        raise RuntimeError("WTA scrape found no live player-v-player matches")

    return {
        "league":"WTA Tour",
        "sourceName":"WTA Official Scores",
        "sourceUrl":official_scores,
        "updatedAt":datetime.now(timezone.utc).isoformat(),
        "note":"Live WTA scores scraped from official WTA score pages.",
        "games":games,
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
    jobs = [("wta", wta_calendar_schedule), ("euroleague", euroleague), ("npb", npb), ("kbo", kbo)]
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
