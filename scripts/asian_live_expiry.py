"""Persistent two-hour live windows; missing feed entries must not reset them."""
from datetime import datetime, timedelta, timezone


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
    except (TypeError, ValueError):
        return None


def expire_entries(entries, previous, now, *, streams=False):
    ledger = dict(previous.get("liveExpiryLedger", {}))
    # Migrate timestamps from the old feed before it is replaced.
    for old in previous.get("streams" if streams else "games", []):
        key = str(old.get("eventId") or "")
        if key and (old.get("firstLiveAt") or old.get("expiresAt")):
            ledger.setdefault(key, {k: old[k] for k in ("firstLiveAt", "expiresAt") if k in old})
    result = []
    for entry in entries:
        if streams and entry.get("leagueKey") != "asian_games":
            result.append(entry)
            continue
        key = str(entry.get("eventId") or "")
        if not key or (not streams and entry.get("state") != "live"):
            result.append(entry)
            continue
        saved = ledger.get(key, {})
        first = timestamp(saved.get("firstLiveAt")) or timestamp(entry.get("firstLiveAt")) or now
        deadline = first + timedelta(hours=2)
        saved_expiry = timestamp(saved.get("expiresAt"))
        if saved_expiry:
            deadline = min(deadline, saved_expiry)
        window = {"firstLiveAt": first.isoformat(), "expiresAt": deadline.isoformat()}
        ledger[key] = window
        entry.update(window)
        if streams:
            entry["stream"].update(window)
        if now >= deadline:
            if streams:
                continue
            entry.update(state="expired", status="Awaiting official result", streams=[], streamsChecked=True, liveExpired=True)
        result.append(entry)
    return result, ledger
