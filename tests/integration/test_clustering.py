from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.app.bootstrap import bootstrap_application
from src.clustering.matcher import MatchableEvent
from src.config.settings import AppSettings


class ClusteringIntegrationTest(unittest.TestCase):
    def test_clustering_service_persists_cluster_and_members(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts = bootstrap_application(AppSettings.from_env(Path(tmp_dir)))
            early_warning = MatchableEvent(
                normalized_event_id=11,
                event_type="early_warning",
                started_at=datetime(2026, 3, 22, 12, 0, tzinfo=timezone.utc),
                location_names={"תל אביב", "רמת גן", "גבעתיים"},
            )
            candidates = [
                MatchableEvent(
                    normalized_event_id=12,
                    event_type="actual_alarm",
                    started_at=datetime(2026, 3, 22, 12, 1, tzinfo=timezone.utc),
                    location_names={"תל אביב", "רמת גן"},
                ),
                MatchableEvent(
                    normalized_event_id=13,
                    event_type="actual_alarm",
                    started_at=datetime(2026, 3, 22, 12, 4, tzinfo=timezone.utc),
                    location_names={"חיפה"},
                ),
            ]

            result = artifacts.clustering_service.cluster_alarm_candidate(early_warning, candidates)

            self.assertIsNotNone(result.cluster_id)
            self.assertEqual(result.match_result.candidate_event_id, 12)

            with sqlite3.connect(artifacts.settings.database_path) as connection:
                cluster_count = connection.execute("SELECT COUNT(*) FROM event_clusters").fetchone()[0]
                member_count = connection.execute("SELECT COUNT(*) FROM cluster_members").fetchone()[0]

            self.assertEqual(cluster_count, 1)
            self.assertEqual(member_count, 2)


if __name__ == "__main__":
    unittest.main()
