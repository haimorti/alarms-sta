from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.app.bootstrap import bootstrap_application
from src.clustering.matcher import MatchableEvent
from src.config.settings import AppSettings
from src.db.raw_events import RawEventInsert, RawEventRepository
from src.geo.risk_windows import RiskWindowDraft


class ProbabilityApiIntegrationTest(unittest.TestCase):
    def test_probability_current_creates_snapshot_with_breakdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = AppSettings.from_env(Path(tmp_dir))
            artifacts = bootstrap_application(settings)
            payload = json.loads(Path("tests/fixtures/raw/sample_alerts_payload.json").read_text(encoding="utf-8"))
            raw_repo = RawEventRepository(settings.database_path)
            raw_event = raw_repo.save(
                RawEventInsert(
                    fetched_at=datetime.fromisoformat("2026-03-22T12:00:00+00:00"),
                    source_payload=payload,
                    source_url=settings.alerts_url,
                    payload_hash="probability-hash",
                )
            )
            normalize_result = artifacts.normalization_service.normalize_raw_event(raw_event.id)
            self.assertEqual(len(normalize_result.normalized_event_ids), 3)

            early_warning = MatchableEvent(
                normalized_event_id=normalize_result.normalized_event_ids[0],
                event_type="early_warning",
                started_at=datetime(2026, 3, 22, 12, 0, tzinfo=timezone.utc),
                location_names={"רמת גן", "אבו גוש"},
            )
            candidates = [
                MatchableEvent(
                    normalized_event_id=normalize_result.normalized_event_ids[1],
                    event_type="actual_alarm",
                    started_at=datetime(2026, 3, 22, 12, 1, tzinfo=timezone.utc),
                    location_names={"רמת גן"},
                )
            ]
            cluster_result = artifacts.clustering_service.cluster_alarm_candidate(early_warning, candidates)
            self.assertIsNotNone(cluster_result.cluster_id)
            artifacts.risk_window_service.record_window(
                RiskWindowDraft(
                    cluster_id=cluster_result.cluster_id,
                    normalized_event_id=normalize_result.normalized_event_ids[0],
                    phase_index=1,
                    phase_label="initial_launch_detection",
                    window_started_at="2026-03-22T12:00:00+00:00",
                    window_ended_at="2026-03-22T12:00:05+00:00",
                    geometry_kind="ellipse",
                    geometry_payload='{\"major_axis\": 10, \"minor_axis\": 5}',
                    centroid_lat=32.08,
                    centroid_lon=34.81,
                    area_scale=1.0,
                    trajectory_confidence=0.35,
                    notes="Wide initial uncertainty window",
                )
            )
            artifacts.risk_window_service.record_window(
                RiskWindowDraft(
                    cluster_id=cluster_result.cluster_id,
                    normalized_event_id=normalize_result.normalized_event_ids[1],
                    phase_index=2,
                    phase_label="refined_warning_zone",
                    window_started_at="2026-03-22T12:00:05+00:00",
                    window_ended_at=None,
                    geometry_kind="ellipse",
                    geometry_payload='{\"major_axis\": 4, \"minor_axis\": 2}',
                    centroid_lat=32.07,
                    centroid_lon=34.82,
                    area_scale=0.4,
                    trajectory_confidence=0.78,
                    notes="Refined later-stage estimate",
                )
            )

            current = artifacts.api_service.probability_current("רמת גן")
            self.assertIsNotNone(current)
            snapshot = current["snapshot"]
            self.assertIn("spatial_score", snapshot)
            self.assertIn("historical_score", snapshot)
            self.assertIn("weighted_score", snapshot)
            self.assertEqual(snapshot["historical_label"], "high")
            self.assertEqual(current["risk_window"]["phase_label"], "refined_warning_zone")

            history = artifacts.api_service.probability_history("רמת גן")
            self.assertEqual(len(history["history"]), 1)

            with sqlite3.connect(settings.database_path) as connection:
                snapshot_count = connection.execute("SELECT COUNT(*) FROM probability_snapshots").fetchone()[0]
            self.assertEqual(snapshot_count, 1)

    def test_api_health_and_search_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts = bootstrap_application(AppSettings.from_env(Path(tmp_dir)))
            health = artifacts.api_service.health()
            search = artifacts.api_service.settlements_search("אבו גוש")

            self.assertEqual(health["status"], "ok")
            self.assertGreaterEqual(len(search), 1)
            self.assertEqual(search[0]["name_he"], "אבו גוש")


if __name__ == "__main__":
    unittest.main()
