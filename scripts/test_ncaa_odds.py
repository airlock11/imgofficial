#!/usr/bin/env python3
"""Offline regression coverage for NCAA Philippines odds discovery and refresh."""
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("img_odds_update", ROOT / "scripts/update_odds.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

now = datetime.now(timezone.utc)
start = (now + timedelta(minutes=10)).isoformat()
data = {"leagues": {"ncaa_ph": {"games": [
    {"date": start, "state": "scheduled"},
    {"date": (now - timedelta(hours=2)).isoformat(), "state": "final"},
]}}}
mod.SPECIAL_SPORTS = Mock(read_text=Mock(return_value=json.dumps(data)))
interval, reason = mod.ncaa_ph_refresh_plan(now)
assert interval == timedelta(minutes=5) and reason == "ncaa-ph-game-window", (interval, reason)
mod.pba_refresh_plan = lambda now=None: (timedelta(hours=6), "routine")
assert mod.active_odds_refresh_plan(now) == (timedelta(minutes=5), "ncaa-ph-game-window")

data["leagues"]["ncaa_ph"]["games"][0]["state"] = "live"
mod.SPECIAL_SPORTS.read_text.return_value = json.dumps(data)
assert mod.ncaa_ph_refresh_plan(now) == (timedelta(minutes=5), "ncaa-ph-live")

# A Philippines fixture may be discoverable even if the tournament listing omits it.
fixture_rows = [
    {"tournamentId": 777, "tournamentName": "NCAA Division I", "categoryName": "USA"},
    {"tournamentId": 123, "tournamentName": "NCAA Seniors", "categoryName": "Philippines",
     "liveFixtures": 1},
    {"tournamentId": 124, "tournamentName": "NCAA Women", "categoryName": "Philippines",
     "futureFixtures": 10},
]
calls = []
def get_json(path, params):
    calls.append((path, params))
    if path == "/tournaments":
        return []
    if path == "/fixtures":
        return fixture_rows
    raise AssertionError(path)
mod.get_json = get_json
assert mod.discover_ncaa_ph_tournament() == 123
assert [p for p, _ in calls] == ["/tournaments", "/fixtures"]
assert calls[1][1]["sportId"] == 11
assert "from" in calls[1][1] and "to" in calls[1][1]
assert mod._ncaa_ph_tournament_id([fixture_rows[0], fixture_rows[2]]) is None
print("PASS: NCAA Philippines game-aware odds refresh and verified league discovery")
