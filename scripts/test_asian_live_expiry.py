import unittest
from datetime import datetime, timedelta, timezone
from asian_live_expiry import expire_entries


class ExpiryTests(unittest.TestCase):
    def test_verified_stream_has_no_two_hour_hard_expiry_and_fallback_does(self):
        now = datetime(2026, 9, 22, tzinfo=timezone.utc)

        def stream(status="verified", last_verified=None):
            item = {
                "eventId": "asian-video",
                "leagueKey": "asian_games",
                "verificationStatus": status,
                "stream": {
                    "watchUrl": "https://www.youtube.com/watch?v=abcdefghijk",
                    "verificationStatus": status,
                },
            }
            if last_verified:
                item["lastVerifiedLiveAt"] = last_verified
                item["stream"]["lastVerifiedLiveAt"] = last_verified
            return item

        entries, ledger = expire_entries([stream()], {}, now, streams=True)
        self.assertEqual(len(entries), 1)
        self.assertNotIn("expiresAt", entries[0])
        self.assertEqual(entries[0]["verificationStatus"], "verified")

        # A later positive verification keeps the stream alive beyond two hours.
        entries, ledger = expire_entries(
            [stream()],
            {"liveExpiryLedger": ledger},
            now + timedelta(hours=3),
            streams=True,
        )
        self.assertEqual(len(entries), 1)
        self.assertNotIn("expiresAt", entries[0])

        # If verification becomes unavailable, the last successful verification
        # starts a two-hour fallback window.
        last_verified = now.isoformat()
        fallback = stream("fallback", last_verified)
        entries, ledger = expire_entries(
            [fallback],
            {"liveExpiryLedger": {}},
            now + timedelta(minutes=119),
            streams=True,
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(
            entries[0]["fallbackExpiresAt"],
            (now + timedelta(hours=2)).isoformat(),
        )

        entries, ledger = expire_entries(
            [stream("fallback", last_verified)],
            {"liveExpiryLedger": ledger},
            now + timedelta(hours=2),
            streams=True,
        )
        self.assertEqual(entries, [])

        # If YouTube later positively verifies the same video as live, it can
        # reappear; a previous fallback timeout must not permanently suppress it.
        entries, ledger = expire_entries(
            [stream("verified")],
            {"liveExpiryLedger": ledger},
            now + timedelta(hours=3),
            streams=True,
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["verificationStatus"], "verified")
        self.assertNotIn("fallbackExpiresAt", entries[0])

    def test_scores_survive_state_changes_without_reset_or_invented_results(self):
        now = datetime(2026, 9, 22, tzinfo=timezone.utc)
        games, ledger = expire_entries([{"eventId": "game", "state": "live", "homeScore": "2"}], {}, now)
        _, ledger = expire_entries([{"eventId": "game", "state": "scheduled"}], {"liveExpiryLedger": ledger}, now + timedelta(hours=1))
        games, ledger = expire_entries([{"eventId": "game", "state": "live", "homeScore": "2", "streams": [{}]}], {"liveExpiryLedger": ledger}, now + timedelta(hours=2))
        self.assertEqual(games[0]["state"], "expired")
        self.assertEqual(games[0]["homeScore"], "2")
        self.assertEqual(games[0]["streams"], [])
        other = {"eventId": "ncaa", "leagueKey": "ncaa_ph", "stream": {}}
        entries, _ = expire_entries([other], {}, now, streams=True)
        self.assertEqual(entries, [other])
        self.assertNotIn("expiresAt", other)


if __name__ == "__main__":
    unittest.main()
