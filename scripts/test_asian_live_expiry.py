import unittest
from datetime import datetime, timedelta, timezone
from asian_live_expiry import expire_entries


class ExpiryTests(unittest.TestCase):
    def test_stream_refresh_missing_and_rediscovery_never_extend_window(self):
        now = datetime(2026, 9, 22, tzinfo=timezone.utc)
        def stream():
            return {"eventId": "asian-video", "leagueKey": "asian_games", "stream": {"watchUrl": "https://www.youtube.com/watch?v=abcdefghijk"}}
        entries, ledger = expire_entries([stream()], {}, now, streams=True)
        deadline = entries[0]["expiresAt"]
        entries, ledger = expire_entries([stream()], {"liveExpiryLedger": ledger}, now + timedelta(minutes=119), streams=True)
        self.assertEqual(entries[0]["expiresAt"], deadline)
        self.assertEqual(entries[0]["stream"]["expiresAt"], deadline)
        entries, ledger = expire_entries([], {"liveExpiryLedger": ledger}, now + timedelta(hours=2), streams=True)
        entries, ledger = expire_entries([stream()], {"liveExpiryLedger": ledger}, now + timedelta(hours=3), streams=True)
        self.assertEqual(entries, [])

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
