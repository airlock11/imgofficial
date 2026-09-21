#!/usr/bin/env python3
import io
import json
import re
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image, ImageOps
import pytesseract

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "regional-web.json"
UA = "Mozilla/5.0 (compatible; IMG-Sports-WebUpdater/1.0; +https://imgofficial.com)"
PHT = timezone(timedelta(hours=8))

URLS = {
    "pba": "https://skedcheck.com/pba-games-schedule-scores/",
    "uaap": "https://skedcheck.com/uaap-mens-basketball-schedule-scores/",
    "mpbl_fixtures": "https://www.forebet.com/en/basketball/philippines/mpbl/fixtures",
    "mpbl_results": "https://www.forebet.com/en/basketball/philippines/mpbl/results",
    "nbl_official": "http://nblp.web.geniussports.com/",
    "nbl_facebook": "https://www.facebook.com/nblpilipinas",
    "nbl_facebook_share": "https://www.facebook.com/share/18tLhjYjUv/",
    "nbl_updates": "https://www.findglocal.com/PH/Cabuyao/1997682720482608/NBL-Pilipinas",
    "nblaus": "https://www.nbl.com.au/",
    "vba_results": "https://www.forebet.com/en/basketball/vietnam/results",
    "vba_betexplorer": "https://www.betexplorer.com/basketball/vietnam/vba/",
    "vba_ticket": "https://ticket.vba.vn/team/5",
    "nbl_youtube_feed": "https://www.youtube.com/feeds/videos.xml?channel_id=UCJDBLldRGVJPEvyjJdSHefw",
    "tap": "https://tapdmv.com/tapsports/"
}

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")

def lines(url):
    soup = BeautifulSoup(fetch(url), "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return [re.sub(r"\s+", " ", x).strip() for x in soup.get_text("\n").splitlines() if re.sub(r"\s+", " ", x).strip()]

def load():
    try:
        return json.loads(OUT.read_text("utf-8"))
    except Exception:
        return {"leagues": {}}

def pht_iso_from_dmy(dmy):
    dt = datetime.strptime(dmy, "%d/%m/%Y").replace(hour=12, tzinfo=PHT)
    return dt.isoformat()

def pht_iso_from_month(text, tm=None):
    text = re.sub(r"\s*\|\s*[A-Za-z]+$", "", text).strip()
    dt = datetime.strptime(text, "%B %d, %Y")
    if tm:
        m = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)", tm, re.I)
        if m:
            h, minute = int(m.group(1)), int(m.group(2))
            if m.group(3).upper() == "PM" and h < 12: h += 12
            if m.group(3).upper() == "AM" and h == 12: h = 0
            dt = dt.replace(hour=h, minute=minute)
    else:
        dt = dt.replace(hour=12)
    return dt.replace(tzinfo=PHT).isoformat()

def clean_team(s):
    return re.sub(r"\s+[A-Z]{2,5}$", "", s.strip()).strip()

def parse_pba():
    xs = lines(URLS["pba"])
    games, day = [], None
    date_re = re.compile(r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+2026(?:\s*\|\s*[A-Za-z]+)?$")
    i = 0
    while i < len(xs):
        if date_re.match(xs[i]):
            day = xs[i]; i += 1; continue
        if not day:
            i += 1; continue
        if i + 3 < len(xs) and re.fullmatch(r"\d{2,3}\s*\|\s*\d{2,3}", xs[i+1]) and xs[i+2].upper() == "FINAL":
            first, second = clean_team(xs[i]), clean_team(xs[i+3])
            a, b = [v.strip() for v in xs[i+1].split("|")]
            iso = pht_iso_from_month(day)
            games.append({"eventId":"web-pba-final-"+str(len(games)+1),"date":iso,"displayTime":datetime.fromisoformat(iso).strftime("%b %d · Final").replace(" 0"," "),"away":second,"home":first,"awayScore":b,"homeScore":a,"status":"Final","state":"final","sourceName":"SkedCheck","sourceUrl":URLS["pba"]})
            i += 4; continue
        if i + 2 < len(xs) and re.fullmatch(r"VS\s+\d{1,2}:\d{2}\s*(AM|PM)", xs[i+1], re.I):
            first, second = clean_team(xs[i]), clean_team(xs[i+2])
            tm = xs[i+1][2:].strip()
            iso = pht_iso_from_month(day, tm)
            games.append({"eventId":"web-pba-scheduled-"+str(len(games)+1),"date":iso,"displayTime":datetime.fromisoformat(iso).strftime("%b %d · %I:%M %p").replace(" 0"," "),"away":first,"home":second,"awayScore":"—","homeScore":"—","status":"Scheduled","state":"scheduled","sourceName":"SkedCheck","sourceUrl":URLS["pba"]})
            i += 3; continue
        i += 1
    if not games:
        existing = load().get("leagues", {}).get("pba", {})
        if existing:
            return existing
        raise RuntimeError("No PBA games parsed")
    return {"league":"PBA","season":"2026 Governors' Cup","coverage":"Schedule and final scores","note":"Automatically refreshed from public web schedule/results.","sources":[{"name":"SkedCheck","url":URLS["pba"]},{"name":"PBA Official","url":"https://www.pba.ph/"}],"games":games[:40]}

def parse_uaap():
    xs = lines(URLS["uaap"])
    games, day = [], None
    date_re = re.compile(r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+2026(?:\s*\|\s*.*)?$")
    teams = {
        "ADMU":"Ateneo Blue Eagles",
        "ADU":"Adamson Soaring Falcons",
        "DLSU":"De La Salle Green Archers",
        "FEU":"FEU Tamaraws",
        "NU":"NU Bulldogs",
        "UE":"UE Red Warriors",
        "UP":"UP Fighting Maroons",
        "UST":"UST Growling Tigers",
    }
    def team_name(value):
        value = value.strip()
        return teams.get(value.upper(), clean_team(value))

    for i, x in enumerate(xs):
        if x == "Discover More":
            break
        if date_re.match(x):
            day = x
            continue
        if not day:
            continue

        # SkedCheck renders final scores as:
        # TEAM, SCORE, |, SCORE, FINAL, TEAM
        if x.upper() == "FINAL" and i >= 4 and i + 1 < len(xs):
            if xs[i-2] == "|" and re.fullmatch(r"\d{2,3}", xs[i-3]) and re.fullmatch(r"\d{2,3}", xs[i-1]):
                home, away = team_name(xs[i-4]), team_name(xs[i+1])
                hs, as_ = xs[i-3], xs[i-1]
                tm = xs[i+3] if i+3 < len(xs) and re.fullmatch(r"\d{1,2}:\d{2}\s*(AM|PM)", xs[i+3], re.I) else None
                iso = pht_iso_from_month(day, tm)
                games.append({
                    "eventId":"web-uaap-final-"+str(len(games)+1),
                    "date":iso,
                    "displayTime":datetime.fromisoformat(iso).strftime("%b %d · Final").replace(" 0"," "),
                    "away":away,"home":home,"awayScore":as_,"homeScore":hs,
                    "status":"Final","state":"final",
                    "sourceName":"SkedCheck","sourceUrl":URLS["uaap"]
                })
            continue

        # Upcoming rows render as: TEAM, VS, TIME, TEAM.
        if x.upper() == "VS" and i >= 1 and i + 2 < len(xs):
            tm = xs[i+1]
            if re.fullmatch(r"\d{1,2}:\d{2}\s*(AM|PM)", tm, re.I):
                home, away = team_name(xs[i-1]), team_name(xs[i+2])
                iso = pht_iso_from_month(day, tm)
                games.append({
                    "eventId":"web-uaap-scheduled-"+str(len(games)+1),
                    "date":iso,
                    "displayTime":datetime.fromisoformat(iso).strftime("%b %d · %I:%M %p").replace(" 0"," "),
                    "away":away,"home":home,"awayScore":"—","homeScore":"—",
                    "status":"Scheduled","state":"scheduled",
                    "sourceName":"SkedCheck","sourceUrl":URLS["uaap"]
                })

    games = dedupe_games(games)
    if not games:
        existing = load().get("leagues", {}).get("uaap", {})
        if existing:
            return existing
        raise RuntimeError("No UAAP games parsed")
    scheduled = sorted([g for g in games if g.get("state")=="scheduled"], key=lambda x:x.get("date",""))
    finals = sorted([g for g in games if g.get("state")=="final"], key=lambda x:x.get("date",""), reverse=True)

    # Preserve the last verified standings snapshot until a reliable machine-readable
    # standings source is available in the updater.
    existing = load().get("leagues", {}).get("uaap", {})
    standings = existing.get("standings", []) if isinstance(existing, dict) else []

    return {
        "league":"UAAP",
        "season":"Season 89 Men's Basketball",
        "coverage":"Schedule, final scores and standings",
        "note":"Automatically refreshed from the current UAAP Season 89 public schedule/results page. Live One Sports broadcasts are handled separately by the YouTube live scanner.",
        "sources":[
            {"name":"UAAP Official","url":"https://uaap.org/"},
            {"name":"UAAP Live Stats","url":"https://uaap.livestats.ph/tournaments/uaap-season-89-men-s-basketball"},
            {"name":"SkedCheck","url":URLS["uaap"]},
            {"name":"One Sports","url":"https://www.youtube.com/@OneSportsPHL"}
        ],
        "standings": standings,
        "games": scheduled[:20] + finals[:30]
    }

def parse_forebet(url, state):
    xs = lines(url)
    games, day = [], None
    i = 0
    while i < len(xs):
        if re.fullmatch(r"\d{2}/\d{2}/2026", xs[i]):
            day = xs[i]; i += 1; continue
        if not day:
            i += 1; continue
        if state == "final" and i + 2 < len(xs) and re.fullmatch(r"\d{1,3}\s*:\s*\d{1,3}", xs[i+1]):
            a, b = [v.strip() for v in xs[i+1].split(":")]
            iso = pht_iso_from_dmy(day)
            games.append({"eventId":"web-mpbl-final-"+str(len(games)+1),"date":iso,"displayTime":datetime.fromisoformat(iso).strftime("%b %d · Final").replace(" 0"," "),"away":xs[i+2],"home":xs[i],"awayScore":b,"homeScore":a,"status":"Final","state":"final","sourceName":"Forebet","sourceUrl":url})
            i += 3; continue
        if state == "scheduled" and i + 2 < len(xs) and xs[i+1] == "-":
            iso = pht_iso_from_dmy(day)
            games.append({"eventId":"web-mpbl-scheduled-"+str(len(games)+1),"date":iso,"displayTime":datetime.fromisoformat(iso).strftime("%b %d").replace(" 0"," "),"away":xs[i],"home":xs[i+2],"awayScore":"—","homeScore":"—","status":"Scheduled","state":"scheduled","sourceName":"Forebet","sourceUrl":url})
            i += 3; continue
        i += 1
    return games

def parse_mpbl():
    try:
        games = parse_forebet(URLS["mpbl_fixtures"], "scheduled")[:20] + parse_forebet(URLS["mpbl_results"], "final")[:20]
    except Exception:
        games = []
    if not games:
        existing = load().get("leagues", {}).get("mpbl", {})
        if existing:
            return existing
        raise RuntimeError("No MPBL games parsed")
    return {"league":"MPBL","season":"2026 Season","coverage":"Upcoming fixtures and recent final scores","note":"Automatically refreshed from public MPBL fixture/result pages.","sources":[{"name":"Forebet","url":"https://www.forebet.com/en/basketball/philippines/mpbl"},{"name":"MPBL Official","url":"https://mpbl.com.ph/"}],"games":games}

def nbl_source_lines():
    # Official Facebook first. A block/login wall must never abort NBL updates.
    for url, name in (
        (URLS["nbl_facebook"], "NBL-Pilipinas Official Facebook"),
        (URLS["nbl_facebook_share"], "NBL-Pilipinas Official Facebook"),
        (URLS["nbl_updates"], "NBL-Pilipinas Facebook mirror"),
    ):
        try:
            xs = lines(url)
            joined = " ".join(xs).upper()
            if len(xs) >= 10 and ("NBL" in joined or "PILIPINAS" in joined):
                return xs, name, url
        except Exception:
            continue
    return [], "NBL-Pilipinas Official Facebook", URLS["nbl_facebook"]

NBL_TEAM_ALIASES = {
    "Batangas Barako - Venom Art": ["BATANGAS BARAKO VENOM ART", "BATANGAS BARAKO", "VENOM ART", "BATANGAS"],
    "CamSur Express": ["CAM SUR EXPRESS", "CAMSUR EXPRESS", "CAM SUR", "CAMSUR"],
    "Manila MLB": ["MANILA MLB", "MANILA"],
    "Nueva Ecija Granary Buffalos": ["NUEVA ECIJA GRANARY BUFFALOS", "GRANARY BUFFALOS", "NUEVA ECIJA"],
    "Pangasinan Asinderos": ["PANGASINAN ASINDEROS", "ASINDEROS", "PANGASINAN"],
    "Quezon City Titans": ["QUEZON CITY TITANS", "QUEZON CITY", "QC TITANS"],
    "Quezon Starhorse": ["QUEZON STARHORSE", "QUEZON STAR HORSE", "STARHORSE", "STAR HORSE"],
    "Taguig City Generals": ["TAGUIG CITY GENERALS", "TAGUIG GENERALS", "TAGUIG"],
    "Tikas Kapampangan": ["TIKAS KAPAMPANGAN", "TIKAS KAPANGAN", "KAPAMPANGAN", "PAMPANGA"],
    "Zamboanga Valientes": ["ZAMBOANGA VALIENTES", "VALIENTES", "ZAMBOANGA"]
}

def canonical_nbl_team(value):
    normalized = normalize_ocr_text(value)
    best = None
    best_len = 0
    for team, aliases in NBL_TEAM_ALIASES.items():
        for alias in [team] + aliases:
            a = normalize_ocr_text(alias)
            if not a:
                continue
            if normalized == a or a in normalized or normalized in a:
                if len(a) > best_len:
                    best = team
                    best_len = len(a)
    return best or str(value or "").strip()

def nbl_verified_seed_games():
    # High-confidence 2026 results from public/official sources. These are
    # retained until a newer verified source for the same matchup/date exists.
    return [
        {
            "eventId": "verified-nbl-20260830-starhorse-tikas",
            "date": "2026-08-30T18:00:00+08:00",
            "displayTime": "Aug 30 · Final",
            "away": "Tikas Kapampangan",
            "home": "Quezon Starhorse",
            "awayScore": "84",
            "homeScore": "87",
            "status": "Final",
            "state": "final",
            "sourceName": "NBL-Pilipinas public update",
            "sourceUrl": URLS["nbl_updates"],
        },
        {
            "eventId": "verified-nbl-20260817-pangasinan-nueva-ecija",
            "date": "2026-08-17T18:00:00+08:00",
            "displayTime": "Aug 17 · Final",
            "away": "Nueva Ecija Granary Buffalos",
            "home": "Pangasinan Asinderos",
            "awayScore": "110",
            "homeScore": "129",
            "status": "Final",
            "state": "final",
            "sourceName": "Province of Pangasinan",
            "sourceUrl": "https://www.pangasinan.gov.ph/asinderos-crush-granary-buffalos-129-110-in-nbl-pilipinas-governors-cup/",
        },
    ]

def score_is_known(value):
    return bool(re.fullmatch(r"\d{1,3}", str(value or "").strip()))

def nbl_game_quality(game):
    score = int(score_is_known(game.get("homeScore"))) + int(score_is_known(game.get("awayScore")))
    source = str(game.get("sourceName") or "").lower()
    verified = 2 if ("province of pangasinan" in source or "public update" in source or "facebook image" in source) else 0
    status = 1 if str(game.get("status") or "").strip() else 0
    return score * 10 + verified + status

def dedupe_nbl_games(games):
    # Keep the most informative record for a matchup/day. In particular, a
    # blank-score YouTube replay must never replace a verified scored final.
    chosen = {}
    order = []
    for game in games:
        game = dict(game)
        game["home"] = canonical_nbl_team(game.get("home"))
        game["away"] = canonical_nbl_team(game.get("away"))
        teams = tuple(sorted([normalize_ocr_text(game.get("home")), normalize_ocr_text(game.get("away"))]))
        day = str(game.get("date") or "")[:10]
        key = (teams, day)
        if key not in chosen:
            chosen[key] = game
            order.append(key)
        elif nbl_game_quality(game) > nbl_game_quality(chosen[key]):
            chosen[key] = game
    return [chosen[key] for key in order]

def parse_nbl_official_site():
    # Genius Sports is the league's published official website. Some deployments
    # render data client-side; if usable game rows are present in HTML, collect
    # them. Otherwise log a compact diagnostic and fall back to verified sources.
    try:
        html = fetch(URLS["nbl_official"])
    except Exception as ex:
        print("NBL official site unavailable", type(ex).__name__, str(ex)[:120])
        return []
    soup = BeautifulSoup(html, "html.parser")
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    print("NBL official site fetched", len(html), "bytes", "text", text[:180])
    games = []
    # Conservative parser for explicit date + team + score rows only.
    date_pat = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+2026"
    for dm in re.finditer(date_pat, text, re.I):
        window = text[dm.start():dm.start()+700]
        found = []
        for team, aliases in NBL_TEAM_ALIASES.items():
            pos = min([window.upper().find(a) for a in aliases if window.upper().find(a) >= 0] or [99999])
            if pos < 99999:
                found.append((pos, team))
        found.sort()
        if len(found) < 2:
            continue
        score_match = re.search(r"\b(\d{2,3})\s*[-–:]\s*(\d{2,3})\b", window)
        if not score_match:
            continue
        dt = datetime.strptime(f"{dm.group(1)} {dm.group(2)} 2026", "%B %d %Y").replace(hour=18, tzinfo=PHT)
        home, away = found[0][1], found[1][1]
        a, b = score_match.groups()
        games.append({
            "eventId": "official-nbl-" + dt.strftime("%Y%m%d") + "-" + str(len(games)+1),
            "date": dt.isoformat(),
            "displayTime": dt.strftime("%b %d · Final").replace(" 0", " "),
            "away": away,
            "home": home,
            "awayScore": b,
            "homeScore": a,
            "status": "Final",
            "state": "final",
            "sourceName": "NBL-Pilipinas Official",
            "sourceUrl": URLS["nbl_official"],
        })
    return games

def normalize_ocr_text(value):
    value = re.sub(r"[^A-Z0-9 ]+", " ", str(value or "").upper())
    return re.sub(r"\s+", " ", value).strip()

def teams_in_ocr(text):
    normalized = normalize_ocr_text(text)
    found = []
    for team, aliases in NBL_TEAM_ALIASES.items():
        for alias in aliases:
            if normalize_ocr_text(alias) in normalized:
                found.append(team)
                break
    return found

def nbl_image_candidates(limit=18):
    html = fetch(URLS["nbl_updates"])
    soup = BeautifulSoup(html, "html.parser")
    urls = []

    def add_url(value):
        if not value:
            return
        value = value.strip()
        if value.startswith("//"):
            value = "https:" + value
        elif value.startswith("/"):
            value = urllib.parse.urljoin(URLS["nbl_updates"], value)
        if not re.search(r"https?://img\d*\.findglocal\.com/.+\.(?:jpe?g|png|webp)(?:\?.*)?$", value, re.I):
            return
        if value not in urls:
            urls.append(value)

    for img in soup.find_all("img"):
        add_url(img.get("src"))
        add_url(img.get("data-src"))
        srcset = img.get("srcset") or ""
        for part in srcset.split(","):
            add_url(part.strip().split(" ")[0] if part.strip() else "")
    for a in soup.find_all("a", href=True):
        add_url(a.get("href"))

    return urls[:limit]

def download_image(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/avif,image/webp,image/png,image/jpeg,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=25) as r:
        data = r.read(8 * 1024 * 1024)
    image = Image.open(io.BytesIO(data)).convert("RGB")
    if max(image.size) < 1800:
        scale = min(3, max(1, 1800 // max(image.size)))
        if scale > 1:
            image = image.resize((image.width * scale, image.height * scale))
    gray = ImageOps.grayscale(image)
    return ImageOps.autocontrast(gray)

def ocr_image(url):
    image = download_image(url)
    return pytesseract.image_to_string(image, config="--psm 6")

def ocr_date_time(text):
    upper = text.upper()
    now = datetime.now(PHT)
    date_value = None

    m = re.search(r"\b(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+(\d{1,2})(?:,\s*(2026))?\b", upper)
    if m:
        year = int(m.group(3) or now.year)
        date_value = datetime.strptime(f"{m.group(1)} {m.group(2)} {year}", "%B %d %Y")
    else:
        m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](2026)\b", upper)
        if m:
            month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
            date_value = datetime(year, month, day)
        elif "TODAY" in upper:
            date_value = now.replace(tzinfo=None)

    if not date_value:
        return None

    tm = re.search(r"\b(\d{1,2}):(\d{2})\s*(AM|PM)\b", upper)
    if tm:
        hour, minute = int(tm.group(1)), int(tm.group(2))
        if tm.group(3) == "PM" and hour < 12:
            hour += 12
        if tm.group(3) == "AM" and hour == 12:
            hour = 0
        date_value = date_value.replace(hour=hour, minute=minute)
    else:
        date_value = date_value.replace(hour=12, minute=0)

    return date_value.replace(tzinfo=PHT)

def score_near_team(ocr_lines, team):
    aliases = NBL_TEAM_ALIASES.get(team, [team])
    normalized_aliases = [normalize_ocr_text(a) for a in aliases]
    for index, line in enumerate(ocr_lines):
        normalized = normalize_ocr_text(line)
        if not any(alias in normalized for alias in normalized_aliases):
            continue
        for offset in (0, 1, -1, 2):
            pos = index + offset
            if pos < 0 or pos >= len(ocr_lines):
                continue
            nums = [int(x) for x in re.findall(r"\b(\d{2,3})\b", ocr_lines[pos])]
            nums = [x for x in nums if 40 <= x <= 200]
            if nums:
                return str(nums[-1])
    return None

def image_game_records():
    games = []
    scanned = 0
    matched = 0

    for url in nbl_image_candidates():
        try:
            text = ocr_image(url)
        except Exception:
            continue

        scanned += 1
        upper = text.upper()
        teams = teams_in_ocr(text)
        if len(teams) < 2:
            continue

        dt = ocr_date_time(text)
        lines_ocr = [x.strip() for x in text.splitlines() if x.strip()]
        is_final = bool(re.search(r"\b(FINAL|FINAL SCORE|FULL TIME)\b", upper))
        is_schedule = bool(re.search(r"\b(SCHEDULE|GAME ?DAY|GAMEDAY|UPCOMING|TIP ?OFF|MATCHUP|VS\.?)\b", upper))

        if is_final:
            home, away = teams[0], teams[1]
            home_score = score_near_team(lines_ocr, home)
            away_score = score_near_team(lines_ocr, away)
            if not home_score or not away_score or home_score == away_score:
                continue
            if not dt:
                dt = datetime.now(PHT).replace(hour=12, minute=0, second=0, microsecond=0)
            games.append({
                "eventId": "ocr-nbl-final-" + str(len(games) + 1),
                "date": dt.isoformat(),
                "displayTime": dt.strftime("%b %d · Final").replace(" 0", " "),
                "away": away,
                "home": home,
                "awayScore": away_score,
                "homeScore": home_score,
                "status": "Final",
                "state": "final",
                "sourceName": "NBL-Pilipinas Facebook image",
                "sourceUrl": URLS["nbl_facebook"]
            })
            matched += 1
            continue

        if is_schedule and dt:
            # A schedule graphic may contain several team pairs. Pair teams in
            # reading order; only create records when the graphic includes a date.
            for i in range(0, len(teams) - 1, 2):
                home, away = teams[i], teams[i + 1]
                games.append({
                    "eventId": "ocr-nbl-scheduled-" + str(len(games) + 1),
                    "date": dt.isoformat(),
                    "displayTime": dt.strftime("%b %d · %I:%M %p").replace(" 0", " "),
                    "away": away,
                    "home": home,
                    "awayScore": "—",
                    "homeScore": "—",
                    "status": "Scheduled",
                    "state": "scheduled",
                    "sourceName": "NBL-Pilipinas Facebook image",
                    "sourceUrl": URLS["nbl_facebook"]
                })
                matched += 1

    return games, {"images_scanned": scanned, "images_matched": matched}

def dedupe_games(games):
    out = []
    seen = set()
    for game in games:
        teams = tuple(sorted([normalize_ocr_text(game.get("home")), normalize_ocr_text(game.get("away"))]))
        day = str(game.get("date") or "")[:10]
        key = (teams, day, game.get("state"))
        if key in seen:
            continue
        seen.add(key)
        out.append(game)
    return out

def parse_nbl_youtube_feed():
    games = []
    try:
        xml = fetch(URLS["nbl_youtube_feed"])
    except Exception:
        return games

    soup = BeautifulSoup(xml, "xml")
    for entry in soup.find_all("entry")[:20]:
        title = entry.title.get_text(" ", strip=True) if entry.title else ""
        published = entry.published.get_text(" ", strip=True) if entry.published else ""
        link_tag = entry.find("link")
        link = link_tag.get("href") if link_tag else "https://www.youtube.com/@nblpilipinas"
        m = re.search(
            r"NBL\s+Governor'?s\s+Cup\s+2026\s*\|\s*"
            r"(January|February|March|April|May|June|July|August|September|October|November|December)"
            r"\s+(\d{1,2}),\s*2026\s*\|\s*(.+?)\s+vs\.?\s+(.+)$",
            title,
            re.I
        )
        if not m:
            continue
        dt = datetime.strptime(f"{m.group(1)} {m.group(2)} 2026", "%B %d %Y").replace(hour=18, tzinfo=PHT)
        home = canonical_nbl_team(m.group(3).strip())
        away = canonical_nbl_team(m.group(4).strip())
        now = datetime.now(PHT)
        is_past = dt <= now
        games.append({
            "eventId": "yt-nbl-" + dt.strftime("%Y%m%d") + "-" + str(len(games)+1),
            "date": dt.isoformat(),
            "displayTime": dt.strftime("%b %d").replace(" 0", " "),
            "away": away,
            "home": home,
            "awayScore": "—",
            "homeScore": "—",
            "status": "Replay available" if is_past else "Scheduled",
            "state": "final" if is_past else "scheduled",
            "sourceName": "NBL-Pilipinas YouTube",
            "sourceUrl": link
        })
    return games

def parse_nbl():
    xs, score_source_name, score_source_url = nbl_source_lines()
    games, day, pair = [], None, []
    known_aliases = [normalize_ocr_text(a) for values in NBL_TEAM_ALIASES.values() for a in values]

    for x in xs:
        if re.fullmatch(r"\d{2}/\d{2}/2026", x):
            day, pair = x, []
            continue
        m = re.fullmatch(r"(.{3,60}?)\s+(\d{2,3})", x)
        if day and m:
            team = m.group(1).strip()
            upper = normalize_ocr_text(team)
            if any(alias in upper or upper in alias for alias in known_aliases):
                pair.append((team, m.group(2)))
                if len(pair) == 2:
                    iso = pht_iso_from_dmy(day)
                    games.append({"eventId":"web-nbl-final-"+str(len(games)+1),"date":iso,"displayTime":datetime.fromisoformat(iso).strftime("%b %d · Final").replace(" 0"," "),"away":pair[1][0],"home":pair[0][0],"awayScore":pair[1][1],"homeScore":pair[0][1],"status":"Final","state":"final","sourceName":score_source_name,"sourceUrl":score_source_url})
                    pair = []

    image_meta = {"images_scanned": 0, "images_matched": 0, "facebook_blocked": False}
    try:
        image_games, image_meta = image_game_records()
        games.extend(image_games)
    except Exception as image_error:
        image_meta = {"images_scanned": 0, "images_matched": 0, "facebook_blocked": True, "error": str(image_error)[:160]}

    # Prefer the league's official Genius Sports site when it exposes usable rows.
    games.extend(parse_nbl_official_site())

    # Always retain high-confidence scored results; this also protects against
    # a temporary source outage replacing scores with blank replay metadata.
    games.extend(nbl_verified_seed_games())
    existing_nbl = load().get("leagues", {}).get("nbl", {})
    games.extend([
        g for g in existing_nbl.get("games", [])
        if g.get("state") == "final"
        and score_is_known(g.get("homeScore"))
        and score_is_known(g.get("awayScore"))
    ])

    # Official NBL YouTube feed remains usable without an API key and keeps
    # current matchups available even when Facebook blocks GitHub Actions.
    games.extend(parse_nbl_youtube_feed())

    broadcast = []
    try:
        tx = lines(URLS["tap"])
        current = None
        for x in tx:
            if re.fullmatch(r"(September|October|November|December)\s+\d{1,2},\s+2026\s*\|\s*[A-Za-z]+", x):
                current = x.split("|")[0].strip()
            elif current and "NBL PILIPINAS" in x.upper():
                tm = re.match(r"(\d{1,2}:\d{2}\s*(?:AM|PM))\s*\|", x, re.I)
                if tm:
                    broadcast.append({"date":datetime.strptime(current,"%B %d, %Y").strftime("%Y-%m-%d"),"time":tm.group(1),"source":"Tap Sports"})
    except Exception:
        pass

    games = dedupe_nbl_games(games)
    scheduled = sorted([g for g in games if g.get("state") == "scheduled"], key=lambda x: x.get("date", ""))
    finals = sorted([g for g in games if g.get("state") == "final"], key=lambda x: x.get("date", ""), reverse=True)
    games = scheduled[:12] + finals[:30]
    if not games and not broadcast:
        existing = load().get("leagues", {}).get("nbl", {})
        if existing:
            existing["image_scan"] = image_meta
            existing["note"] = "The latest automated scan found no new high-confidence NBL Facebook score/schedule graphics, so the last verified NBL data was preserved."
            return existing
        raise RuntimeError("No NBL data parsed")

    return {
        "league":"NBL-Pilipinas",
        "season":"2026 Governor's Cup",
        "coverage":"Official site, verified public scores, YouTube matchups and broadcast schedule",
        "note":"IMG prioritizes the official NBL-Pilipinas site and verified scored results, preserves confirmed scores through source outages, and uses the official YouTube feed for current matchups when Facebook blocks automated access.",
        "sources":[
            {"name":"NBL-Pilipinas Official","url":URLS["nbl_official"]},
            {"name":"NBL-Pilipinas Official Facebook","url":URLS["nbl_facebook"]},
            {"name":"NBL-Pilipinas Facebook share link","url":URLS["nbl_facebook_share"]},
            {"name":"Facebook-image mirror","url":URLS["nbl_updates"]},
            {"name":"NBL-Pilipinas YouTube","url":"https://www.youtube.com/channel/UCJDBLldRGVJPEvyjJdSHefw"},
            {"name":"Tap Sports","url":URLS["tap"]}
        ],
        "image_scan": image_meta,
        "broadcast":broadcast[:20],
        "games":games
    }


NBL_AUS_TEAMS = {
    "MEL": "Melbourne United",
    "ADL": "Adelaide 36ers",
    "PER": "Perth Wildcats",
    "SEM": "South East Melbourne Phoenix",
    "NZL": "New Zealand Breakers",
    "ILL": "Illawarra Hawks",
    "SYD": "Sydney Kings",
    "CNS": "Cairns Taipans",
    "TAS": "Tasmania JackJumpers",
    "BRI": "Brisbane Bullets",
}

def parse_nbl_australia():
    xs = lines(URLS["nblaus"])
    text = " ".join(xs)
    # Official NBL homepage publishes compact rows such as:
    # RD 1 Sat, Sep 19 7:30 pm AEST MEL 95 ADL 97
    pattern = re.compile(
        r"RD\s+\d+\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s*"
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+"
        r"(\d{1,2}):(\d{2})\s*(am|pm)\s+(?:AEST|AEDT)\s+"
        r"([A-Z]{3})(?:\s+(\d{2,3}))?\s+([A-Z]{3})(?:\s+(\d{2,3}))?",
        re.I,
    )
    games = []
    for m in pattern.finditer(text):
        mon, day, hh, mm, ap, a_code, a_score, b_code, b_score = m.groups()
        a_code, b_code = a_code.upper(), b_code.upper()
        if a_code not in NBL_AUS_TEAMS or b_code not in NBL_AUS_TEAMS:
            continue
        dt = datetime.strptime(f"{mon} {day} 2026 {hh}:{mm} {ap.upper()}", "%b %d %Y %I:%M %p")
        # NBL's published national schedule is displayed in AEST/AEDT. September
        # dates here are AEST (+10); the website shows the supplied displayTime.
        dt = dt.replace(tzinfo=timezone(timedelta(hours=10)))
        final = bool(a_score and b_score)
        games.append({
            "eventId": "web-nblaus-" + dt.strftime("%Y%m%d%H%M") + "-" + a_code + "-" + b_code,
            "date": dt.isoformat(),
            "displayTime": dt.strftime("%b %d · Final" if final else "%b %d · %I:%M %p").replace(" 0", " "),
            "away": NBL_AUS_TEAMS[b_code],
            "home": NBL_AUS_TEAMS[a_code],
            "awayScore": b_score or "—",
            "homeScore": a_score or "—",
            "status": "Final" if final else "Scheduled",
            "state": "final" if final else "scheduled",
            "sourceName": "NBL Australia",
            "sourceUrl": "https://www.nbl.com.au/schedule",
        })
    if not games:
        existing = load().get("leagues", {}).get("nblaus", {})
        if existing:
            return existing
        raise RuntimeError("No NBL Australia games parsed")
    return {
        "league": "NBL Australia",
        "season": "2026-27 NBL27",
        "coverage": "Official NBL schedule and results",
        "note": "Automatically refreshed from the official NBL Australia schedule/results pages.",
        "sources": [
            {"name": "NBL Australia Official", "url": "https://www.nbl.com.au/"},
            {"name": "NBL Schedule", "url": "https://schedule.nbl.com.au/nbl"},
        ],
        "games": dedupe_games(games)[:30],
    }

VBA_TEAMS = [
    "Hanoi Buffaloes",
    "Saigon Heat",
    "Nhatrang Dolphins",
    "Nha Trang Dolphins",
    "Ho Chi Minh City Wings",
    "Can Tho Catfish",
    "Cantho Catfish",
    "Da Nang Dragons",
]

def parse_vba_results_from(url):
    xs = lines(url)
    games = []
    day = None
    i = 0
    while i < len(xs):
        if re.fullmatch(r"\d{2}/\d{2}/2026", xs[i]):
            day = xs[i]
            i += 1
            continue
        if day and i + 2 < len(xs) and re.fullmatch(r"\d{1,3}\s*:\s*\d{1,3}", xs[i+1]):
            home, away = xs[i].strip(), xs[i+2].strip()
            if any(t.lower() in home.lower() for t in VBA_TEAMS) and any(t.lower() in away.lower() for t in VBA_TEAMS):
                hs, as_ = [v.strip() for v in xs[i+1].split(":")]
                dt = datetime.strptime(day, "%d/%m/%Y").replace(hour=19, tzinfo=timezone(timedelta(hours=7)))
                games.append({
                    "eventId": "web-vba-final-" + dt.strftime("%Y%m%d") + "-" + str(len(games)+1),
                    "date": dt.isoformat(),
                    "displayTime": dt.strftime("%b %d · Final").replace(" 0", " "),
                    "away": away,
                    "home": home,
                    "awayScore": as_,
                    "homeScore": hs,
                    "status": "Final",
                    "state": "final",
                    "sourceName": "VBA results",
                    "sourceUrl": url,
                })
                i += 3
                continue
        i += 1
    return games

def parse_vba_ticket_fixtures():
    try:
        xs = lines(URLS["vba_ticket"])
    except Exception:
        return []
    text = " ".join(xs)
    games = []
    pattern = re.compile(
        r"(Saigon Heat)\s+vs\s+(Hanoi Buffaloes)\s+(\d{1,2}):(\d{2})\s+(\d{2}/\d{2}/2026)",
        re.I,
    )
    for m in pattern.finditer(text):
        home, away, hh, mm, day = m.groups()
        dt = datetime.strptime(day + f" {hh}:{mm}", "%d/%m/%Y %H:%M").replace(tzinfo=timezone(timedelta(hours=7)))
        games.append({
            "eventId": "web-vba-scheduled-" + dt.strftime("%Y%m%d%H%M"),
            "date": dt.isoformat(),
            "displayTime": dt.strftime("%b %d · %I:%M %p").replace(" 0", " "),
            "away": away,
            "home": home,
            "awayScore": "—",
            "homeScore": "—",
            "status": "Scheduled",
            "state": "scheduled",
            "sourceName": "VBA Ticket",
            "sourceUrl": URLS["vba_ticket"],
        })
    return games

def parse_vba():
    games = []
    # Public result mirrors are used because vba.vn renders fixtures dynamically.
    for url in (URLS["vba_results"], URLS["vba_betexplorer"]):
        try:
            parsed = parse_vba_results_from(url)
            if parsed:
                games.extend(parsed[:20])
                break
        except Exception:
            continue
    games.extend(parse_vba_ticket_fixtures())

    # If a public results mirror blocks the runner, keep the last verified
    # final scores while still accepting newly parsed official ticket fixtures.
    existing = load().get("leagues", {}).get("vba", {})
    if existing:
        games.extend([
            g for g in existing.get("games", [])
            if g.get("state") == "final"
        ])

    games = dedupe_games(games)
    if not games:
        if existing:
            return existing
        raise RuntimeError("No VBA games parsed")

    games = sorted(games, key=lambda x: x.get("date", ""), reverse=True)
    scheduled = sorted([g for g in games if g.get("state") == "scheduled"], key=lambda x: x.get("date", ""))
    finals = sorted([g for g in games if g.get("state") == "final"], key=lambda x: x.get("date", ""), reverse=True)
    return {
        "league": "VBA",
        "season": "2026 Season",
        "coverage": "2026 VBA Finals fixtures and recent results",
        "note": "Automatically refreshed from public VBA schedule and results sources.",
        "sources": [
            {"name": "VBA Official", "url": "https://vba.vn/fixtures"},
            {"name": "VBA Ticket", "url": URLS["vba_ticket"]},
            {"name": "Forebet Results", "url": URLS["vba_results"]},
        ],
        "games": (scheduled[:10] + finals[:20]),
    }

def main():
    data = load()
    data.setdefault("leagues", {})
    errors = {}
    for key, fn in [("pba", parse_pba), ("uaap", parse_uaap), ("mpbl", parse_mpbl), ("nbl", parse_nbl), ("nblaus", parse_nbl_australia), ("vba", parse_vba)]:
        try:
            fresh = fn()
            if fresh.get("games") or fresh.get("broadcast"):
                data["leagues"][key] = fresh
        except Exception as e:
            errors[key] = str(e)
    data["updated_at"] = datetime.now(PHT).isoformat(timespec="seconds")
    data["refresh_minutes"] = 30
    data["errors"] = errors
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({"updated_at":data["updated_at"],"errors":errors,"counts":{k:len(v.get("games",[])) for k,v in data["leagues"].items()}}, ensure_ascii=False))

if __name__ == "__main__":
    main()
