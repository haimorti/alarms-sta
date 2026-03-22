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


if __name__ == "__main__":
    unittest.main()
