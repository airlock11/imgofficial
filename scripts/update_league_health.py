#!/usr/bin/env python3
"""IMG league coverage audit.

Do not mistake a freshly rewritten JSON file for up-to-date league fixtures.
Public visibility depends on published, dated fixtures and source availability.
Do not delete historical league data when a public listing is suspended.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime.now(timezone.utc)
OUT = ROOT / "league-data-health.json"
PAST_WINDOW = timedelta(days=21)
UPCOMING_WINDOW = timedelta(days=90)

# Limited tournaments and genuinely seasonal calendars retain archive listings
# between seasons. For continuing leagues, a 21-day fixture gap is suspicious.
SEASONAL = {
    "asian_games", "wnba", "mls", "atp", "wta", "australian_open",
    "wimbledon", "us_open", "ipl", "bigbash", "cricket_world_cup",
    "volleyball_w", "volleyball_m", "npb", "kbo", "iihf", "f1",
    "motogp", "formulae", "ufc",
}

def load(name):
    try:
        return json.loads((ROOT / name).read_text("utf-8"))
    except (OSError, ValueError):
        return {}

def parse_date(value):
    if not value:
        return None
    try:
        value = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None

def league_entry(data, key):
    leagues = data.get("leagues", {})
    return leagues.get(key, {}) if isinstance(leagues, dict) else {}

def has_any(item, *keys):
    return isinstance(item, dict) and any(bool(item.get(k)) for k in keys)

registry = load("league-data-registry.json")
sources = {
    "extended": load("extended-sports-data.json"),
    "regional": load("regional-web.json"),
    "special": load("special-sports-data.json"),
    "espn-cache": load("football-espn-cache.json"),
}
stats = load("stats-data.json")
rows = {}
for key, meta in registry.get("leagues", {}).items():
    entries = [(name, league_entry(data, key)) for name, data in sources.items()]
    entries = [(name, item) for name, item in entries if isinstance(item, dict) and item]
    games = [g for _, item in entries for g in item.get("games", []) if isinstance(g, dict)]
    dates = sorted({
        event_date for game in games
        if (event_date := parse_date(game.get("date") or game.get("startTime")))
    })
    active_dates = [
        dt for dt in dates
        if NOW - PAST_WINDOW <= dt <= NOW + UPCOMING_WINDOW
    ]
    previous = [dt for dt in dates if dt < NOW]
    future = [dt for dt in dates if dt >= NOW]
    pipeline = meta.get("pipeline", "")
    manually_hidden = meta.get("publicVisible") is False

    if manually_hidden:
        status = "unavailable"
    elif pipeline == "direct_espn":
        # ESPN is fetched at runtime and may have a working proxy fallback.
        # A local snapshot cannot establish whether either endpoint works.
        status = "live-api-unverified"
    elif not games:
        status = "needs-source"
    elif active_dates:
        status = "active-fixtures"
    elif key in SEASONAL:
        status = "off-season"
    else:
        status = "stale-fixtures"

    visible = not manually_hidden and status not in ("needs-source", "stale-fixtures")
    if manually_hidden:
        note = meta.get("visibilityReason", "Feed unavailable")
    elif pipeline == "direct_espn":
        note = "Client-side API and its fallback require independent live checks."
    elif status == "needs-source":
        note = "No published scores or scheduled fixtures from known sources."
    elif status == "stale-fixtures":
        note = "Latest recorded fixtures are too old; a JSON update is not a new fixture."
    elif status == "off-season":
        note = "Seasonal calendar: historical data is preserved during the break."
    else:
        note = "Dated fixtures are present near the current coverage window."

    rows[key] = {
        "label": meta.get("label", key),
        "sport": meta.get("sport", ""),
        "pipeline": pipeline,
        "automatic": bool(meta.get("automatic")),
        "status": status,
        "publicVisible": visible,
        "fixtureCount": len(games),
        "recentOrUpcomingFixtureCount": len(active_dates),
        "lastRecordedFixtureAt": previous[-1].isoformat() if previous else None,
        "nextRecordedFixtureAt": future[0].isoformat() if future else None,
        "sourceFiles": [name for name, _ in entries],
        "statisticsPublished": has_any(league_entry(stats, key), "groups", "leaders"),
        "standingsPublished": any(has_any(item, "standings") for _, item in entries),
        "rankingsPublished": any(has_any(item, "rankings", "ranking", "titleholders", "medals") for _, item in entries),
        "note": note,
    }

summary = {
    "leagues": len(rows),
    "visible": sum(1 for x in rows.values() if x["publicVisible"]),
    "suspended": sum(1 for x in rows.values() if not x["publicVisible"]),
    "activeFixtures": sum(1 for x in rows.values() if x["status"] == "active-fixtures"),
    "staleFixtures": sum(1 for x in rows.values() if x["status"] == "stale-fixtures"),
    "needsSource": sum(1 for x in rows.values() if x["status"] == "needs-source"),
    "liveApiUnverified": sum(1 for x in rows.values() if x["status"] == "live-api-unverified"),
    "offSeason": sum(1 for x in rows.values() if x["status"] == "off-season"),
}
previous_report = load("league-data-health.json")
last_report = parse_date(previous_report.get("updatedAt"))
# Avoid committing a new report on every 5-minute scheduled run when
# the underlying publication decisions and source fixtures are unchanged.
if (previous_report.get("summary") == summary and
        previous_report.get("leagues") == rows and
        last_report and NOW - last_report < timedelta(hours=6)):
    print(json.dumps({"unchanged": True, **summary}))
else:
    payload = {
        "updatedAt": NOW.isoformat(),
        "policy": registry.get("policy", {}),
        "summary": summary,
        "leagues": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", "utf-8")
    print(json.dumps(summary))
