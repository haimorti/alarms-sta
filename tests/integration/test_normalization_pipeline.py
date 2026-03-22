from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from src.app.bootstrap import bootstrap_application
from src.config.settings import AppSettings
from src.db.raw_events import RawEventInsert, RawEventRepository


class NormalizationPipelineIntegrationTest(unittest.TestCase):
    def test_normalize_raw_event_persists_events_and_locations(self) -> None:
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
                    payload_hash="pipeline-hash",
                )
            )

            result = artifacts.normalization_service.normalize_raw_event(raw_event.id)

            self.assertEqual(len(result.normalized_event_ids), 3)
            self.assertEqual(result.unresolved_names, ["תל אביב"])

            with sqlite3.connect(settings.database_path) as connection:
                event_count = connection.execute("SELECT COUNT(*) FROM normalized_events").fetchone()[0]
                location_count = connection.execute("SELECT COUNT(*) FROM event_locations").fetchone()[0]
                parse_status = connection.execute(
                    "SELECT parse_status FROM raw_events WHERE id = ?",
                    (raw_event.id,),
                ).fetchone()[0]

            self.assertEqual(event_count, 3)
            self.assertGreaterEqual(location_count, 5)
            self.assertEqual(parse_status, "parsed")


if __name__ == "__main__":
    unittest.main()
