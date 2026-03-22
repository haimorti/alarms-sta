from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from src.config.settings import AppSettings


class AppSettingsTest(unittest.TestCase):
    def test_from_env_uses_project_root_and_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = AppSettings.from_env(Path(tmp_dir))

            self.assertEqual(settings.project_root, Path(tmp_dir).resolve())
            self.assertEqual(settings.raw_data_dir, Path(tmp_dir).resolve() / "data" / "raw")
            self.assertEqual(settings.normalized_data_dir, Path(tmp_dir).resolve() / "data" / "normalized")
            self.assertEqual(settings.database_path, Path(tmp_dir).resolve() / "data" / "alarms_sta.db")
            self.assertEqual(settings.polling.interval_seconds, 3.0)
            self.assertTrue(settings.polling.archive_raw_payloads)
            self.assertEqual(settings.matching.max_candidate_window_seconds, 180)
            self.assertFalse(settings.debug_mode)

    def test_from_env_reads_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            overrides = {
                "ALARMS_STA_POLL_INTERVAL": "1.5",
                "ALARMS_STA_REQUEST_TIMEOUT": "9",
                "ALARMS_STA_MAX_RETRIES": "5",
                "ALARMS_STA_ARCHIVE_RAW": "0",
                "ALARMS_STA_USER_AGENT": "test-agent",
                "ALARMS_STA_MATCH_WINDOW": "240",
                "ALARMS_STA_MIN_OVERLAP": "0.65",
                "ALARMS_STA_STRONG_SUBSET": "0.9",
                "ALARMS_STA_LOW_THRESHOLD": "25",
                "ALARMS_STA_HIGH_THRESHOLD": "75",
                "ALARMS_STA_SPATIAL_WEIGHT": "0.7",
                "ALARMS_STA_HISTORICAL_WEIGHT": "0.3",
                "ALARMS_STA_DEBUG": "true",
            }
            previous = {key: os.environ.get(key) for key in overrides}
            try:
                os.environ.update(overrides)
                settings = AppSettings.from_env(Path(tmp_dir))
            finally:
                for key, value in previous.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

            self.assertEqual(settings.polling.interval_seconds, 1.5)
            self.assertEqual(settings.polling.request_timeout_seconds, 9.0)
            self.assertEqual(settings.polling.max_retries, 5)
            self.assertFalse(settings.polling.archive_raw_payloads)
            self.assertEqual(settings.polling.user_agent, "test-agent")
            self.assertEqual(settings.matching.max_candidate_window_seconds, 240)
            self.assertEqual(settings.matching.minimum_overlap_ratio, 0.65)
            self.assertEqual(settings.matching.strong_subset_ratio, 0.9)
            self.assertEqual(settings.scoring.low_threshold, 25)
            self.assertEqual(settings.scoring.high_threshold, 75)
            self.assertEqual(settings.scoring.spatial_weight, 0.7)
            self.assertEqual(settings.scoring.historical_weight, 0.3)
            self.assertTrue(settings.debug_mode)


if __name__ == "__main__":
    unittest.main()
