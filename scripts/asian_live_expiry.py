"""Asian Games live-state bookkeeping.

Asian Games entries are never expired by a fixed elapsed-time rule.
They remain live only when the upstream scanner/source reports them live.
"""
from datetime import datetime, timezone


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
    except (TypeError, ValueError):
        return None


def expire_entries(entries, previous, now, *, streams=False):
    ledger = dict(previous.get("liveExpiryLedger", {}))

    # Preserve useful verification timestamps, while deleting legacy fixed-expiry fields.
    for key, saved in list(ledger.items()):
        if not isinstance(saved, dict):
            continue
        saved = dict(saved)
        saved.pop("expiresAt", None)
        saved.pop("fallbackExpiresAt", None)
        ledger[key] = saved

    for old in previous.get("streams" if streams else "games", []):
        key = str(old.get("eventId") or "")
        if not key:
            continue
        saved = dict(ledger.get(key, {}))
        for field in ("firstLiveAt", "lastVerifiedLiveAt"):
            value = old.get(field) or (old.get("stream", {}) if streams else {}).get(field)
            if value and field not in saved:
                saved[field] = value
        saved.pop("expiresAt", None)
        saved.pop("fallbackExpiresAt", None)
        if saved:
            ledger[key] = saved

    result = []
    for entry in entries:
        if streams and entry.get("leagueKey") != "asian_games":
            result.append(entry)
            continue

        key = str(entry.get("eventId") or "")
        if not key:
            result.append(entry)
            continue

        if streams:
            stream = entry.setdefault("stream", {})
            first = (
                timestamp(entry.get("firstLiveAt"))
                or timestamp(stream.get("firstLiveAt"))
                or timestamp(ledger.get(key, {}).get("firstLiveAt"))
                or now
            )
            verified_at = (
                timestamp(entry.get("lastVerifiedLiveAt"))
                or timestamp(stream.get("lastVerifiedLiveAt"))
                or timestamp(ledger.get(key, {}).get("lastVerifiedLiveAt"))
                or now
            )
            saved = dict(ledger.get(key, {}))
            saved.update(
                firstLiveAt=first.isoformat(),
                lastVerifiedLiveAt=verified_at.isoformat(),
            )
            saved.pop("expiresAt", None)
            saved.pop("fallbackExpiresAt", None)
            ledger[key] = saved

            entry["firstLiveAt"] = first.isoformat()
            entry["lastVerifiedLiveAt"] = verified_at.isoformat()
            stream["firstLiveAt"] = first.isoformat()
            stream["lastVerifiedLiveAt"] = verified_at.isoformat()
            for obj in (entry, stream):
                obj.pop("expiresAt", None)
                obj.pop("fallbackExpiresAt", None)

        # Score/live state is controlled by the source. Never mutate it by age.
        result.append(entry)

    return result, ledger
