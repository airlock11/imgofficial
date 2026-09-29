#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

MANILA = timezone(timedelta(hours=8))
IDLE_DISCOVERY_MINUTES = 180


def parse_dt(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=MANILA)
        return dt.astimezone(MANILA)
    except Exception:
        return None


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="tat-official.json")
    ap.add_argument("--event", default=os.getenv("GITHUB_EVENT_NAME", "schedule"))
    args = ap.parse_args()

    data = load(args.data)
    now = datetime.now(timezone.utc).astimezone(MANILA)
    today = now.date()
    today_games = []
    for game in data.get("games") or []:
        dt = parse_dt(game.get("date"))
        if dt and dt.date() == today:
            today_games.append(game)

    game_day = bool(today_games)
    auto = data.get("automation") or {}
    schedule = auto.get("scheduleAware") or {}
    last_slow = parse_dt(schedule.get("lastSlowCheckAt") or auto.get("lastSlowCheckAt"))
    slow_due = last_slow is None or (now - last_slow) >= timedelta(minutes=IDLE_DISCOVERY_MINUTES)

    manual = args.event != "schedule"
    run_slow = manual or slow_due
    run_update = manual or game_day or slow_due

    next_game = None
    future = []
    for game in data.get("games") or []:
        dt = parse_dt(game.get("date"))
        if dt and dt > now and str(game.get("state") or "").lower() in {"scheduled", "pre", "pre-event"}:
            future.append(dt)
    if future:
        next_game = min(future).isoformat(timespec="seconds")

    outputs = {
        "run_update": str(run_update).lower(),
        "run_slow": str(run_slow).lower(),
        "game_day": str(game_day).lower(),
        "today_game_count": str(len(today_games)),
        "next_game_at": next_game or "",
        "mode": "game-day" if game_day else "idle",
    }
    for key, value in outputs.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
