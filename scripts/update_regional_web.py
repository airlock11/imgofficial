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
    "mpbl_fixtures": "https://www.forebet.com/en/basketball/philippines/mpbl/fixtures",
    "mpbl_results": "https://www.forebet.com/en/basketball/philippines/mpbl/results",
    "nbl_facebook": "https://www.facebook.com/nblpilipinas",
    "nbl_facebook_share": "https://www.facebook.com/share/18tLhjYjUv/",
    "nbl_updates": "https://www.findglocal.com/PH/Cabuyao/1997682720482608/NBL-Pilipinas",
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
    # Official NBL-Pilipinas Facebook is the primary source. Facebook can
    # return a login wall to automated requests, so fall back to a public
    # mirror of the same public posts when readable post text is unavailable.
    for url in (URLS["nbl_facebook"], URLS["nbl_facebook_share"]):
        try:
            xs = lines(url)
            joined = " ".join(xs).upper()
            if len(xs) >= 20 and ("NBL" in joined or "PILIPINAS" in joined):
                return xs, "NBL-Pilipinas Official Facebook", URLS["nbl_facebook"]
        except Exception:
            pass
    return lines(URLS["nbl_updates"]), "NBL-Pilipinas Facebook mirror", URLS["nbl_updates"]

NBL_TEAM_ALIASES = {
    "Quezon Starhorse": ["QUEZON STARHORSE", "STARHORSE"],
    "Tikas Kapampangan": ["TIKAS KAPAMPANGAN", "TIKAS KAPANGAN", "KAPAMPANGAN"],
    "Pangasinan Asinderos": ["PANGASINAN ASINDEROS", "ASINDEROS"],
    "Nueva Ecija Granary Buffalos": ["NUEVA ECIJA GRANARY BUFFALOS", "GRANARY BUFFALOS", "NUEVA ECIJA"],
    "CamSur Express": ["CAM SUR EXPRESS", "CAMSUR EXPRESS"],
    "Zamboanga Valientes": ["ZAMBOANGA VALIENTES", "VALIENTES"],
    "Quezon City": ["QUEZON CITY"],
    "Taguig City Generals": ["TAGUIG CITY GENERALS", "TAGUIG GENERALS"],
    "Manila MLB": ["MANILA MLB"],
    "Zambales Constructicons": ["ZAMBALES CONSTRUCTICONS", "CONSTRUCTICONS"],
    "Maximus Bacoor Cavite": ["MAXIMUS BACOOR CAVITE", "MAXIMUS BACOOR"],
    "Santa Rosa Eridanus": ["SANTA ROSA ERIDANUS", "ERIDANUS"]
}

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

    image_meta = {"images_scanned": 0, "images_matched": 0}
    try:
        image_games, image_meta = image_game_records()
        games.extend(image_games)
    except Exception:
        pass

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

    games = dedupe_games(games)
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
        "coverage":"Official Facebook image scan, public scores and broadcast schedule",
        "note":"The updater scans recent NBL-Pilipinas Facebook-uploaded graphics for final scores and schedules. It only adds image-derived games when teams plus score/date information can be read confidently.",
        "sources":[
            {"name":"NBL-Pilipinas Official Facebook","url":URLS["nbl_facebook"]},
            {"name":"NBL-Pilipinas Facebook share link","url":URLS["nbl_facebook_share"]},
            {"name":"Facebook-image mirror","url":URLS["nbl_updates"]},
            {"name":"NBL-Pilipinas YouTube","url":"https://www.youtube.com/channel/UCJDBLldRGVJPEvyjJdSHefw"},
            {"name":"Tap Sports","url":URLS["tap"]}
        ],
        "image_scan": image_meta,
        "broadcast":broadcast[:20],
        "games":games[:30]
    }

def main():
    data = load()
    data.setdefault("leagues", {})
    errors = {}
    for key, fn in [("pba", parse_pba), ("mpbl", parse_mpbl), ("nbl", parse_nbl)]:
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
