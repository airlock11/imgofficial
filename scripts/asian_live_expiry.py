"""Asian Games live-window safety.

Verified YouTube streams stay live for as long as YouTube confirms they are live.
The two-hour window is only a fallback when live-status verification is unavailable.
"""
from datetime import datetime, timedelta, timezone


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
    except (TypeError, ValueError):
        return None


def expire_entries(entries, previous, now, *, streams=False):
    ledger = dict(previous.get("liveExpiryLedger", {}))

    # Migrate timestamps/status from the old feed before it is replaced.
    for old in previous.get("streams" if streams else "games", []):
        key = str(old.get("eventId") or "")
        if not key:
            continue
        saved = dict(ledger.get(key, {}))
        for field in ("firstLiveAt", "lastVerifiedLiveAt", "fallbackExpiresAt", "expiresAt"):
            value = old.get(field) or (old.get("stream", {}) if streams else {}).get(field)
            if value and field not in saved:
                saved[field] = value
        if saved:
            ledger[key] = saved

    result = []
    for entry in entries:
        if streams and entry.get("leagueKey") != "asian_games":
            result.append(entry)
            continue

        key = str(entry.get("eventId") or "")
        if not key or (not streams and entry.get("state") != "live"):
            result.append(entry)
            continue

        saved = dict(ledger.get(key, {}))
        first = timestamp(saved.get("firstLiveAt")) or timestamp(entry.get("firstLiveAt")) or now

        if streams:
            stream = entry.setdefault("stream", {})
            verification = str(
                entry.get("verificationStatus")
                or stream.get("verificationStatus")
                or "verified"
            ).lower()

            if verification == "fallback":
                last_verified = (
                    timestamp(entry.get("lastVerifiedLiveAt"))
                    or timestamp(stream.get("lastVerifiedLiveAt"))
                    or timestamp(saved.get("lastVerifiedLiveAt"))
                    or first
                )
                fallback_deadline = last_verified + timedelta(hours=2)
                saved_deadline = timestamp(saved.get("fallbackExpiresAt"))
                if saved_deadline:
                    fallback_deadline = min(fallback_deadline, saved_deadline)

                saved.update(
                    firstLiveAt=first.isoformat(),
                    lastVerifiedLiveAt=last_verified.isoformat(),
                    fallbackExpiresAt=fallback_deadline.isoformat(),
                )
                ledger[key] = saved

                entry.update(
                    firstLiveAt=first.isoformat(),
                    lastVerifiedLiveAt=last_verified.isoformat(),
                    fallbackExpiresAt=fallback_deadline.isoformat(),
                    verificationStatus="fallback",
                )
                stream.update(
                    firstLiveAt=first.isoformat(),
                    lastVerifiedLiveAt=last_verified.isoformat(),
                    fallbackExpiresAt=fallback_deadline.isoformat(),
                    verificationStatus="fallback",
                )
                entry.pop("expiresAt", None)
                stream.pop("expiresAt", None)

                if now >= fallback_deadline:
                    continue

                result.append(entry)
                continue

            # A positively verified live stream has no fixed two-hour expiry.
            verified_at = (
                timestamp(entry.get("lastVerifiedLiveAt"))
                or timestamp(stream.get("lastVerifiedLiveAt"))
                or now
            )
            saved.update(
                firstLiveAt=first.isoformat(),
                lastVerifiedLiveAt=verified_at.isoformat(),
            )
            saved.pop("fallbackExpiresAt", None)
            saved.pop("expiresAt", None)
            ledger[key] = saved

            entry.update(
                firstLiveAt=first.isoformat(),
                lastVerifiedLiveAt=verified_at.isoformat(),
                verificationStatus="verified",
            )
            stream.update(
                firstLiveAt=first.isoformat(),
                lastVerifiedLiveAt=verified_at.isoformat(),
                verificationStatus="verified",
            )
            for obj in (entry, stream):
                obj.pop("expiresAt", None)
                obj.pop("fallbackExpiresAt", None)

            result.append(entry)
            continue

        # Non-stream Asian Games live data keeps the original two-hour guard.
        deadline = first + timedelta(hours=2)
        saved_expiry = timestamp(saved.get("expiresAt"))
        if saved_expiry:
            deadline = min(deadline, saved_expiry)
        window = {"firstLiveAt": first.isoformat(), "expiresAt": deadline.isoformat()}
        ledger[key] = window
        entry.update(window)
        if now >= deadline:
            entry.update(
                state="expired",
                status="Awaiting official result",
                streams=[],
                streamsChecked=True,
                liveExpired=True,
            )
        result.append(entry)

    return result, ledger
