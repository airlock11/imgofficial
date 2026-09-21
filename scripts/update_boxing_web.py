#!/usr/bin/env python3
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "boxing-web-data.json"
UA = "Mozilla/5.0 (compatible; IMG-Boxing-Web-Updater/1.2; +https://imgofficial.com)"

SOURCES = [
    {
        "name": "Premier Boxing Champions",
        "url": "https://www.premierboxingchampions.com/boxing-schedule",
    },
    {
        "name": "Matchroom Boxing",
        "url": "https://www.matchroomboxing.com/events/",
    },
]

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

VS_RE = re.compile(r"^(.{2,70}?)\s+vs\.?\s+(.{2,70})$", re.I)
DATE_PATTERNS = [
    re.compile(r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)(?:day)?[,]?\s+([A-Za-z]{3,9})\s+(\d{1,2})[,]?\s+(20\d{2})\b", re.I),
    re.compile(r"\b(\d{1,2})\s+([A-Za-z]{3,9})(?:\s+(20\d{2}))?\b", re.I),
    re.compile(r"\b([A-Za-z]{3,9})\s+(\d{1,2})(?:[,]?\s+(20\d{2}))?\b", re.I),
]
TIME_RE = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*(AM|PM)\s*(ET|PT|CT|GMT|BST)?\b", re.I)

def fetch_html(url):
    req = Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    with urlopen(req, timeout=35) as response:
        return response.read().decode("utf-8", "replace")

def clean(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()

def parse_year(month, day, explicit_year=None):
    now = datetime.now(timezone.utc)
    if explicit_year:
        return int(explicit_year)
    year = now.year
    try:
        candidate = datetime(year, month, day, tzinfo=timezone.utc)
        if candidate.timestamp() < now.timestamp() - 45 * 86400:
            year += 1
    except Exception:
        pass
    return year

def parse_date(text):
    text = clean(text)
    for idx, pattern in enumerate(DATE_PATTERNS):
        m = pattern.search(text)
        if not m:
            continue
        if idx == 0:
            month_s, day_s, year_s = m.group(1), m.group(2), m.group(3)
        elif idx == 1:
            day_s, month_s, year_s = m.group(1), m.group(2), m.group(3)
        else:
            month_s, day_s, year_s = m.group(1), m.group(2), m.group(3)
        month = MONTHS.get(month_s.lower())
        if not month:
            continue
        day = int(day_s)
        year = parse_year(month, day, year_s)
        try:
            dt = datetime(year, month, day, 12, 0, tzinfo=timezone.utc)
        except ValueError:
            continue
        return dt, m.group(0)
    return None, ""

def context_for(tag):
    best = clean(tag.get_text(" ", strip=True))
    node = tag
    for _ in range(6):
        node = getattr(node, "parent", None)
        if not node:
            break
        txt = clean(node.get_text(" ", strip=True))
        if len(txt) > len(best):
            best = txt
        if len(txt) >= 120 and any(p.search(txt) for p in DATE_PATTERNS):
            return txt[:1200]
    return best[:1200]

def extract_time_label(context):
    m = TIME_RE.search(context or "")
    if not m:
        return ""
    hh = m.group(1)
    mm = m.group(2) or "00"
    ampm = m.group(3).upper()
    zone = (m.group(4) or "").upper()
    return f"{int(hh)}:{mm} {ampm}" + (f" {zone}" if zone else "")

def slug(value):
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:80]

def split_fighters(title):
    title = clean(title).replace("versus", "vs")
    if len(re.findall(r"\bvs\.?\b", title, flags=re.I)) != 1:
        return None
    m = VS_RE.match(title)
    if not m:
        return None
    left = clean(m.group(1)).strip("-–— ")
    right = clean(m.group(2)).strip("-–— ")
    if not left or not right:
        return None
    bad = ("looking for", "fight night", "watch", "live on")
    if any(x in left.lower() for x in bad) or any(x in right.lower() for x in bad):
        return None
    return left, right

def extract_fights(source):
    html = fetch_html(source["url"])
    soup = BeautifulSoup(html, "html.parser")
    now = datetime.now(timezone.utc)
    fights = []
    seen = set()

    candidates = soup.find_all(["h1", "h2", "h3", "h4", "h5", "a", "strong"])
    for tag in candidates:
        title = clean(tag.get_text(" ", strip=True))
        fighters = split_fighters(title)
        if not fighters:
            continue
        one, two = fighters
        context = context_for(tag)
        dt, date_label = parse_date(context)
        if not dt:
            continue
        # Official web cache is for current/upcoming cards. Results remain covered
        # by the API cache and can be added from web pages separately later.
        if dt.timestamp() < now.timestamp() - 12 * 3600:
            continue

        key = (slug(one), slug(two), dt.date().isoformat())
        reverse = (slug(two), slug(one), dt.date().isoformat())
        if key in seen or reverse in seen:
            continue
        seen.add(key)

        time_label = extract_time_label(context)
        display = dt.strftime("%b %-d")
        if time_label:
            display += " · " + time_label
        else:
            display += " · Time TBA"

        fights.append({
            "id": f"web-{slug(source['name'])}-{dt.date().isoformat()}-{slug(one)}-{slug(two)}",
            "title": f"{one} vs. {two}",
            "date": dt.isoformat().replace("+00:00", "Z"),
            "displayTime": display,
            "status": "NOT_STARTED",
            "sourceName": source["name"],
            "sourceUrl": source["url"],
            "event": {
                "title": source["name"],
                "location": "",
                "venue": "",
            },
            "fighters": {
                "fighter_1": {"name": one, "winner": False},
                "fighter_2": {"name": two, "winner": False},
            },
            "results": {
                "outcome": None,
                "outcome_long": None,
                "round": None,
                "time": None,
                "scores": [],
            },
        })

    fights.sort(key=lambda x: x.get("date") or "")
    return fights[:60]

def main():
    existing = {}
    try:
        existing = json.loads(OUT.read_text("utf-8"))
    except Exception:
        existing = {}

    all_fights = []
    errors = {}
    source_counts = {}
    existing_rows = existing.get("fights") or []
    for source in SOURCES:
        try:
            rows = extract_fights(source)
            if not rows:
                rows = [
                    row for row in existing_rows
                    if row.get("sourceName") == source["name"]
                    and str(row.get("date") or "")[:10] >= datetime.now(timezone.utc).date().isoformat()
                ]
                if rows:
                    errors[source["name"]] = "Parser returned no current rows; retained last verified official schedule"
                else:
                    errors[source["name"]] = "No current fights parsed"
            source_counts[source["name"]] = len(rows)
            all_fights.extend(rows)
        except Exception as exc:
            rows = [
                row for row in existing_rows
                if row.get("sourceName") == source["name"]
                and str(row.get("date") or "")[:10] >= datetime.now(timezone.utc).date().isoformat()
            ]
            if rows:
                source_counts[source["name"]] = len(rows)
                all_fights.extend(rows)
                errors[source["name"]] = "Fetch failed; retained last verified official schedule"
            else:
                errors[source["name"]] = str(exc)[:240]

    deduped = []
    seen = set()
    for fight in all_fights:
        one = slug(fight.get("fighters", {}).get("fighter_1", {}).get("name", ""))
        two = slug(fight.get("fighters", {}).get("fighter_2", {}).get("name", ""))
        day = str(fight.get("date") or "")[:10]
        key = tuple(sorted((one, two))) + (day,)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(fight)

    # Never wipe a working cache if the official sites temporarily change markup.
    if not deduped:
        if existing.get("fights"):
            print(json.dumps({"kept_existing": True, "errors": errors}))
            return
        raise RuntimeError("No official web boxing fights could be parsed")

    out = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Official boxing websites",
        "sources": SOURCES,
        "source_counts": source_counts,
        "errors": errors,
        "fights": deduped,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({
        "updated_at": out["updated_at"],
        "fights": len(deduped),
        "source_counts": source_counts,
        "errors": errors,
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
