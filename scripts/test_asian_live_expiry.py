import unittest
from datetime import datetime, timedelta, timezone
from asian_live_expiry import expire_entries


class ExpiryTests(unittest.TestCase):
    def test_asian_games_stream_has_no_fixed_time_expiry(self):
        now = datetime(2026, 9, 22, tzinfo=timezone.utc)
        stream = {
            "eventId": "asian-video",
            "leagueKey": "asian_games",
            "verificationStatus": "verified",
            "stream": {
                "watchUrl": "https://www.youtube.com/watch?v=abcdefghijk",
                "verificationStatus": "verified",
            },
        }

        entries, ledger = expire_entries([stream], {}, now, streams=True)
        self.assertEqual(len(entries), 1)
        self.assertNotIn("expiresAt", entries[0])
        self.assertNotIn("fallbackExpiresAt", entries[0])

        # Elapsed time alone must never remove a stream.
        entries, ledger = expire_entries(
            [stream],
            {"liveExpiryLedger": ledger},
            now + timedelta(hours=12),
            streams=True,
        )
        self.assertEqual(len(entries), 1)
        self.assertNotIn("expiresAt", entries[0])
        self.assertNotIn("fallbackExpiresAt", entries[0])

    def test_asian_games_score_state_is_not_changed_by_age(self):
        now = datetime(2026, 9, 22, tzinfo=timezone.utc)
        game = {"eventId": "game", "state": "live", "homeScore": "2", "streams": [{}]}
        games, ledger = expire_entries([game], {}, now)
        games, ledger = expire_entries(
            [game],
            {"liveExpiryLedger": ledger},
            now + timedelta(hours=12),
        )
        self.assertEqual(games[0]["state"], "live")
        self.assertEqual(games[0]["homeScore"], "2")
        self.assertEqual(games[0]["streams"], [{}])

        other = {"eventId": "ncaa", "leagueKey": "ncaa_ph", "stream": {}}
        entries, _ = expire_entries([other], {}, now, streams=True)
        self.assertEqual(entries, [other])
        self.assertNotIn("expiresAt", other)


if __name__ == "__main__":
    unittest.main()
