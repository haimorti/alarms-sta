from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from src.clustering.matcher import EventMatcher, MatchableEvent, build_matching_policy


class EventMatcherTest(unittest.TestCase):
    def test_match_actual_alarm_prefers_close_subset_candidate(self) -> None:
        matcher = EventMatcher(build_matching_policy(180, 0.5, 0.8))
        start = datetime(2026, 3, 22, 12, 0, tzinfo=timezone.utc)
        early_warning = MatchableEvent(
            normalized_event_id=1,
            event_type="early_warning",
            started_at=start,
            location_names={"תל אביב", "רמת גן", "גבעתיים"},
        )
        candidates = [
            MatchableEvent(
                normalized_event_id=2,
                event_type="actual_alarm",
                started_at=start + timedelta(seconds=40),
                location_names={"תל אביב", "רמת גן"},
            ),
            MatchableEvent(
                normalized_event_id=3,
                event_type="actual_alarm",
                started_at=start + timedelta(seconds=160),
                location_names={"חיפה"},
            ),
        ]

        result = matcher.match_actual_alarm(early_warning, candidates)

        self.assertEqual(result.candidate_event_id, 2)
        self.assertEqual(result.method, "time_overlap_subset")
        self.assertGreater(result.score, 0.7)

    def test_match_actual_alarm_rejects_low_overlap_candidate(self) -> None:
        matcher = EventMatcher(build_matching_policy(180, 0.5, 0.8))
        start = datetime(2026, 3, 22, 12, 0, tzinfo=timezone.utc)
        early_warning = MatchableEvent(
            normalized_event_id=1,
            event_type="early_warning",
            started_at=start,
            location_names={"תל אביב", "רמת גן"},
        )
        candidates = [
            MatchableEvent(
                normalized_event_id=4,
                event_type="actual_alarm",
                started_at=start + timedelta(seconds=60),
                location_names={"חיפה"},
            )
        ]

        result = matcher.match_actual_alarm(early_warning, candidates)

        self.assertEqual(result.candidate_event_id, None)
        self.assertEqual(result.method, "no_match")
        self.assertEqual(result.score, 0.0)


if __name__ == "__main__":
    unittest.main()
