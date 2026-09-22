#!/usr/bin/env python3
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "wta-live.json"
URL = "https://www.wtatennis.com/scores/"

NAME_RE = re.compile(r"^(?:[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ'’-]*\.?\s+){0,3}[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ'’.-]+(?:\s*\(\d+\))?$")
ROUND_RE = re.compile(r"^(?:ROUND OF \d+|QUARTERFINALS?|SEMIFINALS?|FINAL|QUALIFYING.*)$", re.I)
COURT_RE = re.compile(r"^(?:COURT\s*\w+|CENTER COURT|CENTRE COURT|GRANDSTAND|STADIUM.*)$", re.I)
LIVE_RE = re.compile(r"(?:MEDICAL TIMEOUT|\b\d+(?:ST|ND|RD|TH) SET:\s*\d+:\d+|\bSET\s*\d+|LIVE MATCH|LIVE|SUSPENDED)", re.I)
POINT_RE = re.compile(r"^(?:0|15|30|40|AD|AV|A)$", re.I)
SET_RE = re.compile(r"^\d{1,2}(?:\(\d+\)|\^\d+)?$")
SCORE_TOKEN_RE = re.compile(r"^(?:AD|AV|A|\d{1,2}|\d{1,2}\(\d+\)|\d{1,2}\^\d+|[•·—-])$", re.I)

def clean_line(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()

def chrome_dump():
    candidates = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]
    last = None
    for chrome in candidates:
        try:
            proc = subprocess.run([
                chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
                "--disable-dev-shm-usage", "--hide-scrollbars",
                "--window-size=1440,3200", "--virtual-time-budget=22000",
                "--dump-dom", URL
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=50)
            if proc.returncode == 0 and len(proc.stdout) > 3000:
                return proc.stdout
            last = (chrome, proc.returncode, proc.stderr[-500:])
        except Exception as ex:
            last = (chrome, type(ex).__name__, str(ex))
    raise RuntimeError(f"Chrome render failed: {last}")

def smallest_live_blocks(soup):
    blocks = []
    seen = set()
    for node in soup.find_all(string=LIVE_RE):
        element = node.parent
        best = None
        for _ in range(9):
            if not element or not getattr(element, "stripped_strings", None):
                break
            lines = [clean_line(x) for x in element.stripped_strings if clean_line(x)]
            text = "\n".join(lines)
            if 5 <= len(lines) <= 45 and any(ROUND_RE.match(x) for x in lines):
                best = element
                if len(text) < 1100:
                    break
            element = element.parent
        if best is None:
            continue
        text = "\n".join(clean_line(x) for x in best.stripped_strings if clean_line(x))
        key = re.sub(r"\s+", " ", text)
        if key in seen:
            continue
        seen.add(key)
        blocks.append(text)
    return blocks

def player_candidates(lines):
    out = []
    banned = (
        "WTA", "ROUND", "COURT", "SET", "LIVE", "TIMEOUT", "HARD",
        "SINGAPORE", "KOREA", "OPEN", "SEOUL", "UPCOMING", "FINISHED",
        "GRANDSTAND", "CENTER", "CENTRE", "STADIUM", "FILTER", "MATCH"
    )
    for line in lines:
        s = clean_line(line)
        up = s.upper()
        if not s or any(word in up for word in banned):
            continue
        if re.fullmatch(r"[A-Z]{2,3}", s):
            continue
        if SCORE_TOKEN_RE.match(s):
            continue
        if re.fullmatch(r"[\d\s•·()—-]+", s):
            continue
        if NAME_RE.match(s) and any(ch.islower() for ch in s):
            if "." in s or " " in s or out:
                out.append(s)
    deduped = []
    for name in out:
        if name not in deduped:
            deduped.append(name)
    return deduped[:2]

def tokens_after_name(lines, name):
    try:
        index = lines.index(name)
    except ValueError:
        return []
    values = []
    for raw in lines[index + 1:index + 10]:
        s = clean_line(raw)
        if not s:
            continue
        if LIVE_RE.search(s) or ROUND_RE.match(s) or COURT_RE.match(s):
            break
        if SCORE_TOKEN_RE.match(s):
            if s not in {"•", "·", "—", "-"}:
                values.append(s)
            continue
        if NAME_RE.match(s) and any(ch.islower() for ch in s):
            break
    return values

def normalize_point(value):
    value = str(value or "").upper()
    return "AD" if value in {"A", "AV", "ADV"} else value

def parse_score_tokens(tokens):
    if not tokens:
        return {"point": "—", "sets": []}
    values = [normalize_point(x) for x in tokens]
    point = "—"
    sets = values
    if values and POINT_RE.match(values[0]):
        point = values[0]
        sets = values[1:]
    sets = [x for x in sets if SET_RE.match(x)][:5]
    return {"point": point, "sets": sets}

def current_set_from_status(status, away_sets, home_sets):
    match = re.search(r"\b([1-5])(?:ST|ND|RD|TH)\s+SET\b", status or "", re.I)
    if match:
        return int(match.group(1))
    count = max(len(away_sets), len(home_sets), 1)
    return count

def numeric_set(value):
    match = re.match(r"\d+", str(value or ""))
    return int(match.group(0)) if match else 0

def completed_set(a, b):
    av, bv = numeric_set(a), numeric_set(b)
    high, low = max(av, bv), min(av, bv)
    return high >= 6 and (high - low >= 2 or high == 7)

def sets_won(own, opp, current_set):
    won = 0
    for i in range(min(len(own), len(opp))):
        if i + 1 >= current_set:
            break
        if numeric_set(own[i]) > numeric_set(opp[i]) and completed_set(own[i], opp[i]):
            won += 1
    return won

def parse_blocks(blocks):
    games = []
    for index, text in enumerate(blocks):
        lines = [clean_line(x) for x in text.splitlines() if clean_line(x)]
        names = player_candidates(lines)
        if len(names) < 2:
            continue

        round_name = next((x for x in lines if ROUND_RE.match(x)), "")
        court = next((x for x in lines if COURT_RE.match(x)), "")
        live_status = next((x for x in lines if LIVE_RE.search(x) and not ROUND_RE.match(x)), "Live")

        tournament = ""
        for x in lines[:10]:
            if re.search(r"(OPEN|MASTERS|CLASSIC|CHAMPIONSHIPS|TROPHY)", x, re.I) and not ROUND_RE.match(x):
                tournament = x
                break

        away_parts = parse_score_tokens(tokens_after_name(lines, names[0]))
        home_parts = parse_score_tokens(tokens_after_name(lines, names[1]))
        current_set = current_set_from_status(live_status, away_parts["sets"], home_parts["sets"])

        away_current_games = numeric_set(away_parts["sets"][current_set - 1]) if len(away_parts["sets"]) >= current_set else 0
        home_current_games = numeric_set(home_parts["sets"][current_set - 1]) if len(home_parts["sets"]) >= current_set else 0

        games.append({
            "eventId": "wta-scrape-" + str(index) + "-" + re.sub(r"[^a-z0-9]+", "-", ("-".join(names)).lower()).strip("-")[:70],
            "date": datetime.now(timezone.utc).isoformat(),
            "displayTime": tournament or "WTA Live",
            "away": names[0],
            "home": names[1],
            "awayScore": " ".join(away_parts["sets"]) + ((" · " + away_parts["point"]) if away_parts["point"] != "—" else ""),
            "homeScore": " ".join(home_parts["sets"]) + ((" · " + home_parts["point"]) if home_parts["point"] != "—" else ""),
            "awaySets": away_parts["sets"],
            "homeSets": home_parts["sets"],
            "awayPoint": away_parts["point"],
            "homePoint": home_parts["point"],
            "currentSet": current_set,
            "awayCurrentSetGames": away_current_games,
            "homeCurrentSetGames": home_current_games,
            "awaySetsWon": sets_won(away_parts["sets"], home_parts["sets"], current_set),
            "homeSetsWon": sets_won(home_parts["sets"], away_parts["sets"], current_set),
            "round": round_name,
            "court": court,
            "status": " · ".join(x for x in [live_status, round_name, court] if x),
            "state": "live",
            "eventOnly": False,
            "title": tournament or "WTA",
            "sourceName": "WTA Official Scores scrape",
            "sourceUrl": URL,
            "verificationSource": "WTA Official Scores",
            "verificationUrl": URL,
        })

    unique = []
    seen = set()
    for game in games:
        key = "|".join(sorted([game["away"].lower(), game["home"].lower()]))
        if key in seen:
            continue
        seen.add(key)
        unique.append(game)
    return unique

def main():
    html = chrome_dump()
    soup = BeautifulSoup(html, "lxml")
    blocks = smallest_live_blocks(soup)
    games = parse_blocks(blocks)

    body = " ".join(clean_line(x) for x in soup.stripped_strings)
    page_live_count = None
    m = re.search(r"\bLive\s+(\d+)\b", body, re.I)
    if m:
        page_live_count = int(m.group(1))

    if page_live_count and not games:
        raise RuntimeError(f"WTA page reports {page_live_count} live matches but parser found none")

    payload = {
        "special": True,
        "league": "WTA Tour",
        "live": bool(games),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceName": "WTA Official Scores scrape",
        "sourceUrl": URL,
        "verificationSource": "WTA Official Scores",
        "verificationUrl": URL,
        "pageLiveCount": page_live_count,
        "note": "GitHub scrape of the rendered WTA Scores page. Game points, current set number, current-set games and per-set scores are stored separately.",
        "games": games,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", "utf-8")

    print("WTA live blocks:", len(blocks), "matches:", len(games), "page-live-count:", page_live_count)
    for game in games:
        print(
            "LIVE", game["away"], "game", game["awayPoint"], "sets", game["awaySets"],
            "vs", game["home"], "game", game["homePoint"], "sets", game["homeSets"],
            "| current set", game["currentSet"],
            "| games", game["awayCurrentSetGames"], "-", game["homeCurrentSetGames"],
            "|", game["status"]
        )

if __name__ == "__main__":
    main()
