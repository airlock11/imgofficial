#!/usr/bin/env python3
import json
import re
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from bs4 import BeautifulSoup

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
    return [re.sub(r"\\s+", " ", x).strip() for x in soup.get_text("\\n").splitlines() if re.sub(r"\\s+", " ", x).strip()]

def load():
    try:
        return json.loads(OUT.read_text("utf-8"))
    except Exception:
        return {"leagues": {}}

def pht_iso_from_dmy(dmy):
    dt = datetime.strptime(dmy, "%d/%m/%Y").replace(hour=12, tzinfo=PHT)
    return dt.isoformat()

def pht_iso_from_month(text, tm=None):
    text = re.sub(r"\\s*\\|\\s*[A-Za-z]+$", "", text).strip()
    dt = datetime.strptime(text, "%B %d, %Y")
    if tm:
        m = re.search(r"(\\d{1,2}):(\\d{2})\\s*(AM|PM)", tm, re.I)
        if m:
            h, minute = int(m.group(1)), int(m.group(2))
            if m.group(3).upper() == "PM" and h < 12: h += 12
            if m.group(3).upper() == "AM" and h == 12: h = 0
            dt = dt.replace(hour=h, minute=minute)
    else:
        dt = dt.replace(hour=12)
    return dt.replace(tzinfo=PHT).isoformat()

def clean_team(s):
    return re.sub(r"\\s+[A-Z]{2,5}$", "", s.strip()).strip()

def parse_pba():
    xs = lines(URLS["pba"])
    games, day = [], None
    date_re = re.compile(r"^(January|February|March|April|May|June|July|August|September|October|November|December)\\s+\\d{1,2},\\s+2026(?:\\s*\\|\\s*[A-Za-z]+)?$")
    i = 0
    while i < len(xs):
        if date_re.match(xs[i]):
            day = xs[i]; i += 1; continue
        if not day:
            i += 1; continue
        if i + 3 < len(xs) and re.fullmatch(r"\\d{2,3}\\s*\\|\\s*\\d{2,3}", xs[i+1]) and xs[i+2].upper() == "FINAL":
            first, second = clean_team(xs[i]), clean_team(xs[i+3])
            a, b = [v.strip() for v in xs[i+1].split("|")]
            iso = pht_iso_from_month(day)
            games.append({"eventId":"web-pba-final-"+str(len(games)+1),"date":iso,"displayTime":datetime.fromisoformat(iso).strftime("%b %d · Final").replace(" 0"," "),"away":second,"home":first,"awayScore":b,"homeScore":a,"status":"Final","state":"final","sourceName":"SkedCheck","sourceUrl":URLS["pba"]})
            i += 4; continue
        if i + 2 < len(xs) and re.fullmatch(r"VS\\s+\\d{1,2}:\\d{2}\\s*(AM|PM)", xs[i+1], re.I):
            first, second = clean_team(xs[i]), clean_team(xs[i+2])
            tm = xs[i+1][2:].strip()
            iso = pht_iso_from_month(day, tm)
            games.append({"eventId":"web-pba-scheduled-"+str(len(games)+1),"date":iso,"displayTime":datetime.fromisoformat(iso).strftime("%b %d · %I:%M %p").replace(" 0"," "),"away":first,"home":second,"awayScore":"—","homeScore":"—","status":"Scheduled","state":"scheduled","sourceName":"SkedCheck","sourceUrl":URLS["pba"]})
            i += 3; continue
        i += 1
    if not games: raise RuntimeError("No PBA games parsed")
    return {"league":"PBA","season":"2026 Governors' Cup","coverage":"Schedule and final scores","note":"Automatically refreshed from public web schedule/results.","sources":[{"name":"SkedCheck","url":URLS["pba"]},{"name":"PBA Official","url":"https://www.pba.ph/"}],"games":games[:40]}

def parse_forebet(url, state):
    xs = lines(url)
    games, day = [], None
    i = 0
    while i < len(xs):
        if re.fullmatch(r"\\d{2}/\\d{2}/2026", xs[i]):
            day = xs[i]; i += 1; continue
        if not day:
            i += 1; continue
        if state == "final" and i + 2 < len(xs) and re.fullmatch(r"\\d{1,3}\\s*:\\s*\\d{1,3}", xs[i+1]):
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
    games = parse_forebet(URLS["mpbl_fixtures"], "scheduled")[:20] + parse_forebet(URLS["mpbl_results"], "final")[:20]
    if not games: raise RuntimeError("No MPBL games parsed")
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

NBL_NAMES = ["QUEZON STARHORSE","TIKAS KAPAMPANGAN","PANGASINAN ASINDEROS","NUEVA ECIJA GRANARY BUFFALOS","CAM SUR EXPRESS","CAMSUR EXPRESS","ZAMBOANGA VALIENTES","QUEZON CITY","TAGUIG CITY GENERALS","MANILA MLB","ZAMBALES CONSTRUCTICONS","MAXIMUS BACOOR CAVITE","SANTA ROSA ERIDANUS"]

def parse_nbl():
    xs, score_source_name, score_source_url = nbl_source_lines()
    games, day, pair = [], None, []
    for x in xs:
        if re.fullmatch(r"\\d{2}/\\d{2}/2026", x):
            day, pair = x, []
            continue
        m = re.fullmatch(r"(.{3,60}?)\\s+(\\d{2,3})", x)
        if day and m:
            team = m.group(1).strip()
            upper = team.upper()
            if any(n in upper or upper in n for n in NBL_NAMES):
                pair.append((team, m.group(2)))
                if len(pair) == 2:
                    iso = pht_iso_from_dmy(day)
                    games.append({"eventId":"web-nbl-final-"+str(len(games)+1),"date":iso,"displayTime":datetime.fromisoformat(iso).strftime("%b %d · Final").replace(" 0"," "),"away":pair[1][0],"home":pair[0][0],"awayScore":pair[1][1],"homeScore":pair[0][1],"status":"Final","state":"final","sourceName":score_source_name,"sourceUrl":score_source_url})
                    pair = []
    broadcast = []
    try:
        tx = lines(URLS["tap"])
        current = None
        for x in tx:
            if re.fullmatch(r"(September|October|November|December)\\s+\\d{1,2},\\s+2026\\s*\\|\\s*[A-Za-z]+", x):
                current = x.split("|")[0].strip()
            elif current and "NBL PILIPINAS" in x.upper():
                tm = re.match(r"(\\d{1,2}:\\d{2}\\s*(?:AM|PM))\\s*\\|", x, re.I)
                if tm:
                    broadcast.append({"date":datetime.strptime(current,"%B %d, %Y").strftime("%Y-%m-%d"),"time":tm.group(1),"source":"Tap Sports"})
    except Exception:
        pass
    if not games and not broadcast: raise RuntimeError("No NBL data parsed")
    return {"league":"NBL-Pilipinas","season":"2026 Governor's Cup","coverage":"Official Facebook updates, public scores and broadcast schedule","note":"Official NBL-Pilipinas Facebook is checked first. If Facebook blocks automated access, the updater uses public mirrors of the league's Facebook posts plus official YouTube and broadcast listings. Unverified matchups are not invented.","sources":[{"name":"NBL-Pilipinas Official Facebook","url":URLS["nbl_facebook"]},{"name":"NBL-Pilipinas Facebook share link","url":URLS["nbl_facebook_share"]},{"name":"Facebook-post mirror","url":URLS["nbl_updates"]},{"name":"NBL-Pilipinas YouTube","url":"https://www.youtube.com/channel/UCJDBLldRGVJPEvyjJdSHefw"},{"name":"Tap Sports","url":URLS["tap"]}],"broadcast":broadcast[:20],"games":games[:20]}

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
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\\n", "utf-8")
    print(json.dumps({"updated_at":data["updated_at"],"errors":errors,"counts":{k:len(v.get("games",[])) for k,v in data["leagues"].items()}}, ensure_ascii=False))

if __name__ == "__main__":
    main()
