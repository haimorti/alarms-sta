from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from src.app.bootstrap import bootstrap_application
from src.config.settings import AppSettings
from src.ingestion.poller import FetchedPayload


class IngestionIntegrationTest(unittest.TestCase):
    def test_collect_once_archives_and_preserves_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = AppSettings.from_env(Path(tmp_dir))
            artifacts = bootstrap_application(settings)
            service = artifacts.ingestion_service

            payload = json.loads(Path("tests/fixtures/raw/sample_alerts_payload.json").read_text(encoding="utf-8"))
            fetched_at = datetime(2026, 3, 22, 12, 0, tzinfo=timezone.utc)
            fetched_payload = FetchedPayload(
                fetched_at=fetched_at,
                source_url=settings.alerts_url,
                payload_text=json.dumps(payload, ensure_ascii=False),
                payload_hash="abc123hash",
                payload_json=payload,
                http_status=200,
                response_latency_ms=12.5,
            )

            service.fetcher.fetch_once = lambda: fetched_payload
            first = service.collect_once()
            second = service.collect_once()

            self.assertFalse(first.raw_event_record.is_duplicate)
            self.assertTrue(second.raw_event_record.is_duplicate)
            self.assertEqual(second.raw_event_record.duplicate_of_raw_event_id, first.raw_event_record.id)

            with sqlite3.connect(settings.database_path) as connection:
                rows = connection.execute(
                    "SELECT is_duplicate, duplicate_of_raw_event_id, archive_path, source_url FROM raw_events ORDER BY id"
                ).fetchall()

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0][0], 0)
            self.assertEqual(rows[1][0], 1)
            self.assertEqual(rows[1][1], first.raw_event_record.id)
            self.assertTrue(Path(rows[0][2]).exists())
            self.assertEqual(rows[0][3], settings.alerts_url)


if __name__ == "__main__":
    unittest.main()
