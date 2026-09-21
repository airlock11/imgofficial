#!/usr/bin/env python3
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from asian_live_expiry import expire_entries

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "special-sports-data.json"
BASE = "https://results.asiangames2026.org"
JST = timezone(timedelta(hours=9))

TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")
NOC_RE = re.compile(r"^[A-Z]{3}$")
SCORE_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d+)?|\d+:\d+|—|-)$")
FINAL_STATES = {"Official", "Finished", "Final", "Completed"}
LIVE_STATES = {"Running", "Live", "In Progress"}
SCHEDULED_STATES = {"Scheduled", "Start List", "Upcoming", "Not Started"}
LIVE_EXPIRY = timedelta(hours=2)


def clean_lines(text):
    return [re.sub(r"\s+", " ", x).strip() for x in (text or "").splitlines() if re.sub(r"\s+", " ", x).strip()]


def iso_for(day, tm):
    dt = datetime.strptime(day + " " + tm, "%Y-%m-%d %H:%M").replace(tzinfo=JST)
    return dt.isoformat()


def display_time(day, tm):
    dt = datetime.strptime(day + " " + tm, "%Y-%m-%d %H:%M")
    return dt.strftime("%b %d · %I:%M %p").replace(" 0", " ")


def safe_id(value):
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
    return "ag26-web-" + digest


def score_value(value):
    if value is None:
        return "—"
    value = str(value).strip()
    return value if value and value != "-" else "—"


def parse_card_text(discipline, day, text):
    lines = clean_lines(text)
    if lines and lines[0].lower() == discipline.lower():
        lines = lines[1:]
    if lines and lines[0] == "Live":
        lines = lines[1:]

    starts = [i for i, x in enumerate(lines) if TIME_RE.fullmatch(x)]
    games = []
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        seg = lines[start:end]
        if len(seg) < 2:
            continue
        tm = seg[0]
        body = seg[1:]

        status = ""
        if body and body[-1] in FINAL_STATES | LIVE_STATES | SCHEDULED_STATES:
            status = body.pop()
        if status in LIVE_STATES:
            state = "live"
            status_text = "Live"
        elif status in FINAL_STATES:
            state = "final"
            status_text = "Final"
        else:
            state = "scheduled"
            status_text = status or "Scheduled"

        noc_positions = [i for i, x in enumerate(body) if NOC_RE.fullmatch(x)]
        pairs = []
        used_positions = []
        for pos in noc_positions:
            if pos + 1 >= len(body):
                continue
            country = body[pos + 1]
            if NOC_RE.fullmatch(country) or TIME_RE.fullmatch(country):
                continue
            score = "—"
            if pos + 2 < len(body) and SCORE_RE.fullmatch(body[pos + 2]):
                score = score_value(body[pos + 2])
            pairs.append({"code": body[pos], "name": country, "score": score})
            used_positions.append(pos)
            if len(pairs) >= 2:
                break

        first_noc = used_positions[0] if used_positions else len(body)
        meta = body[:first_noc]
        # Keep concise competition detail; venue/table information remains in status.
        event_name = meta[0] if meta else discipline
        round_name = meta[1] if len(meta) > 1 else ""
        match_name = meta[2] if len(meta) > 2 and re.search(r"\b(Game|Match|Heat|Round|Final|Pool|Group)\b", meta[2], re.I) else ""
        venue_start = 3 if match_name else 2
        venue = " · ".join(meta[venue_start:]) if len(meta) > venue_start else ""
        title_parts = [discipline, event_name]
        if round_name and round_name != event_name:
            title_parts.append(round_name)
        if match_name:
            title_parts.append(match_name)
        title = " — ".join(title_parts[:2]) + ((" · " + " · ".join(title_parts[2:])) if len(title_parts) > 2 else "")

        if len(pairs) >= 2:
            away, home = pairs[0], pairs[1]
            key = "|".join([day, discipline, tm, away["code"], home["code"], event_name, round_name])
            rec = {
                "eventId": safe_id(key),
                "date": iso_for(day, tm),
                "displayTime": display_time(day, tm),
                "title": title,
                "away": away["name"],
                "home": home["name"],
                "awayScore": away["score"],
                "homeScore": home["score"],
                "status": status_text + ((" · " + venue) if venue else ""),
                "state": state,
                "sourceName": "Aichi-Nagoya 2026 Official Results",
                "sourceUrl": f"{BASE}/#/schedule/daily/{day}",
            }
        else:
            key = "|".join([day, discipline, tm, title, venue])
            rec = {
                "eventId": safe_id(key),
                "date": iso_for(day, tm),
                "displayTime": display_time(day, tm),
                "title": title,
                "away": event_name or discipline,
                "home": round_name or discipline,
                "awayScore": "—",
                "homeScore": "—",
                "status": status_text + ((" · " + venue) if venue else ""),
                "state": state,
                "eventOnly": True,
                "sourceName": "Aichi-Nagoya 2026 Official Results",
                "sourceUrl": f"{BASE}/#/schedule/daily/{day}",
            }
        games.append(rec)
    return games


def scrape_day(page, day):
    url = f"{BASE}/#/schedule/daily/{day}"
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)

    cards = page.locator(".sch-one-day")
    count = cards.count()
    games = []
    for i in range(count):
        try:
            card = cards.nth(i)
            disc = card.locator(".disc-desc").first.inner_text(timeout=3000).strip()
            if not disc:
                continue
            header = card.locator(".b-collapse-header").first
            collapsed = card.locator('[data-collapse="collapsed"]').count() > 0
            if collapsed:
                header.click(timeout=4000)
                page.wait_for_timeout(250)
            txt = card.inner_text(timeout=5000)
            games.extend(parse_card_text(disc, day, txt))
        except Exception as ex:
            print("Asian Games discipline scrape warning", day, i, repr(ex))
    print("Asian Games day", day, "cards", count, "events", len(games))
    return games


def scrape_live(page, day):
    url = f"{BASE}/#/schedule/live"
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    cards = page.locator(".sch-one-day")
    games = []
    for i in range(cards.count()):
        try:
            card = cards.nth(i)
            disc = card.locator(".disc-desc").first.inner_text(timeout=3000).strip()
            txt = card.inner_text(timeout=5000)
            for g in parse_card_text(disc, day, txt):
                g["state"] = "live"
                g["status"] = re.sub(r"^Final|^Scheduled", "Live", g.get("status", "")) or "Live"
                games.append(g)
        except Exception:
            continue
    print("Asian Games live events", len(games))
    return games


def parse_medals(text):
    lines = clean_lines(text)
    try:
        start = lines.index("B") + 1
    except ValueError:
        return []

    medals = []
    i = start
    while i + 6 < len(lines):
        rank_token = lines[i]
        rank_match = re.fullmatch(r"=?\s*(\d+)", rank_token)
        if not rank_match:
            i += 1
            continue
        if not NOC_RE.fullmatch(lines[i + 1]):
            i += 1
            continue
        country = lines[i + 2]
        nums = lines[i + 3:i + 7]
        if not all(re.fullmatch(r"\d+", x) for x in nums):
            i += 1
            continue
        medals.append({
            "rank": int(rank_match.group(1)),
            "code": lines[i + 1],
            "country": country,
            "gold": int(nums[0]),
            "silver": int(nums[1]),
            "bronze": int(nums[2]),
            "total": int(nums[3]),
        })
        i += 7
    return medals


def scrape_medals(page):
    page.goto(f"{BASE}/#/medals", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    medals = parse_medals(page.locator("body").inner_text(timeout=10000))
    print("Asian Games medal rows", len(medals))
    return medals


def merge_games(*groups):
    by_id = {}
    priority = {"scheduled": 1, "final": 2, "live": 3}
    for group in groups:
        for g in group:
            old = by_id.get(g["eventId"])
            if not old or priority.get(g.get("state"), 0) >= priority.get(old.get("state"), 0):
                by_id[g["eventId"]] = g
    return sorted(by_id.values(), key=lambda x: x.get("date", ""))


def apply_live_expiry(games, previous_games, now):
    """Keep the first live timestamp stable and suppress live state after two hours."""
    previous_by_id = {str(g.get("eventId")): g for g in previous_games if g.get("eventId")}
    for game in games:
        if game.get("state") != "live":
            continue

        old = previous_by_id.get(str(game.get("eventId")), {})
        first_live_raw = old.get("firstLiveAt") or old.get("liveFirstSeenAt")
        try:
            first_live = datetime.fromisoformat(first_live_raw.replace("Z", "+00:00")) if first_live_raw else now
            if first_live.tzinfo is None:
                first_live = first_live.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            first_live = now

        expiry_raw = old.get("expiresAt") or old.get("liveExpiresAt")
        try:
            expiry = datetime.fromisoformat(expiry_raw.replace("Z", "+00:00")) if expiry_raw else first_live + LIVE_EXPIRY
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            expiry = first_live + LIVE_EXPIRY

        game["firstLiveAt"] = first_live.astimezone(timezone.utc).isoformat()
        game["expiresAt"] = expiry.astimezone(timezone.utc).isoformat()
        if now >= expiry:
            # The official result may not be available yet. Remove only the live
            # assertion and stream controls; never invent a final result.
            game["state"] = "expired"
            game["status"] = "Awaiting official result"
            game["streams"] = []
            game["streamsChecked"] = True
            game["liveExpired"] = True
    return games


def main():
    if OUT.exists():
        data = json.loads(OUT.read_text("utf-8"))
    else:
        data = {"leagues": {}}
    leagues = data.setdefault("leagues", {})
    previous = leagues.get("asian_games", {})

    today_dt = datetime.now(JST)
    day_strings = [(today_dt + timedelta(days=d)).strftime("%Y-%m-%d") for d in (-1, 0, 1)]

    all_games = []
    live_games = []
    medals = []

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1200}, locale="en-US")
        for day in day_strings:
            try:
                all_games.extend(scrape_day(page, day))
            except Exception as ex:
                print("Asian Games day scrape failed", day, repr(ex))
        try:
            live_games = scrape_live(page, day_strings[1])
        except Exception as ex:
            print("Asian Games live scrape failed", repr(ex))
        try:
            medals = scrape_medals(page)
        except Exception as ex:
            print("Asian Games medals scrape failed", repr(ex))
        browser.close()

    games = merge_games(all_games, live_games)
    now_dt = datetime.now(timezone.utc)
    if len(games) < 3:
        games = previous.get("games", [])
        print("Asian Games scrape guard: preserving previous games")
    games, expiry_ledger = expire_entries(games, previous, now_dt)
    if len(medals) < 3:
        medals = previous.get("medals", [])
        print("Asian Games scrape guard: preserving previous medals")

    now = now_dt.isoformat()
    leagues["asian_games"] = {
        **previous,
        "liveExpiryLedger": expiry_ledger,
        "sourceName": "Aichi-Nagoya 2026 Official Results",
        "sourceUrl": BASE + "/#/schedule/daily",
        "games": games,
        "medals": medals,
        "medalsUpdated": today_dt.strftime("%Y-%m-%d"),
        "medalSourceUrl": BASE + "/#/medals/standings",
        "officialLinks": {
            "schedule": BASE + "/#/schedule/daily",
            "liveResults": BASE + "/#/schedule/live",
            "medalTable": BASE + "/#/medals/standings",
        },
        "autoUpdateSource": BASE,
        "autoUpdatedAt": now,
        "autoUpdateMethod": "Official results website browser scrape",
    }
    data["updated_at"] = now
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print("Asian Games published", len(games), "events", len(medals), "medal rows")


if __name__ == "__main__":
    main()
