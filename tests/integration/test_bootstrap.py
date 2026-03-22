from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.app.bootstrap import bootstrap_application
from src.config.settings import AppSettings


class BootstrapIntegrationTest(unittest.TestCase):
    def test_bootstrap_creates_directories_and_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = AppSettings.from_env(Path(tmp_dir))
            artifacts = bootstrap_application(settings)

            self.assertTrue(artifacts.settings.raw_data_dir.exists())
            self.assertTrue(artifacts.settings.normalized_data_dir.exists())
            self.assertTrue(artifacts.settings.database_path.exists())

            with sqlite3.connect(artifacts.settings.database_path) as connection:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    ).fetchall()
                }
                probability_columns = {
                    row[1]
                    for row in connection.execute(
                        "PRAGMA table_info(probability_snapshots)"
                    ).fetchall()
                }
                raw_event_columns = {
                    row[1]
                    for row in connection.execute(
                        "PRAGMA table_info(raw_events)"
                    ).fetchall()
                }

            expected_tables = {
                "raw_events",
                "normalized_events",
                "settlements",
                "settlement_aliases",
                "event_locations",
                "event_clusters",
                "cluster_members",
                "probability_snapshots",
            }
            self.assertTrue(expected_tables.issubset(tables))
            self.assertTrue(
                {
                    "spatial_score",
                    "spatial_explanation",
                    "historical_score",
                    "historical_explanation",
                    "weighted_score",
                    "weighted_explanation",
                    "weighting_profile",
                }.issubset(probability_columns)
            )
            self.assertTrue(
                {
                    "source_url",
                    "payload_hash",
                    "http_status",
                    "response_latency_ms",
                    "archive_path",
                    "is_duplicate",
                    "duplicate_of_raw_event_id",
                }.issubset(raw_event_columns)
            )
            self.assertIsNotNone(artifacts.ingestion_service)
            self.assertIsNotNone(artifacts.normalization_service)
            self.assertIsNotNone(artifacts.clustering_service)
            self.assertIsNotNone(artifacts.probability_engine)
            self.assertIsNotNone(artifacts.api_service)
            self.assertGreater(artifacts.seed_import_result.settlements_imported, 0)
            self.assertGreater(artifacts.seed_import_result.aliases_imported, 0)


if __name__ == "__main__":
    unittest.main()
