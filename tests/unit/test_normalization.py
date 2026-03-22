from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.app.bootstrap import bootstrap_application
from src.config.settings import AppSettings
from src.normalization.classifier import classify_record
from src.normalization.parser import parse_alert_payload
from src.types.domain import NormalizedEventType


class NormalizationTest(unittest.TestCase):
    def setUp(self) -> None:
        fixture_path = Path('tests/fixtures/raw/sample_alerts_payload.json')
        self.payload = json.loads(fixture_path.read_text(encoding='utf-8'))

    def test_parse_alert_payload_extracts_records_and_locations(self) -> None:
        records = parse_alert_payload(self.payload)

        self.assertEqual(len(records), 3)
        self.assertEqual(records[0].source_event_id, '1001')
        self.assertEqual(records[0].locations_raw, ['תל אביב', 'רמת גן', 'אבו-גוש'])

    def test_classify_record_distinguishes_warning_alarm_and_clear(self) -> None:
        records = parse_alert_payload(self.payload)

        classifications = [classify_record(record).event_type for record in records]
        self.assertEqual(
            classifications,
            [
                NormalizedEventType.EARLY_WARNING,
                NormalizedEventType.ACTUAL_ALARM,
                NormalizedEventType.CLEAR,
            ],
        )

    def test_normalization_service_resolves_registry_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts = bootstrap_application(AppSettings.from_env(Path(tmp_dir)))
            previews = artifacts.normalization_service.normalize_payload(self.payload)

        first_locations = previews[0].resolved_locations
        self.assertEqual(first_locations[2].raw_name, 'אבו-גוש')
        self.assertEqual(first_locations[2].canonical_name, 'אבו גוש')
        self.assertIn(first_locations[2].resolution_method, {'manual_alias', 'generated_alias', 'manual_alias_normalized', 'normalized_name'})

    def test_classify_record_supports_home_front_command_titles(self) -> None:
        payload = [
            {'title': 'צפויות להתקבל התרעות', 'data': ['נתניה - מזרח']},
            {'title': 'צבע אדום', 'data': ['נתניה - מזרח']},
            {'title': 'האירוע הסתיים', 'data': ['נתניה - מזרח']},
        ]

        records = parse_alert_payload(payload)
        classifications = [classify_record(record).event_type for record in records]
        self.assertEqual(
            classifications,
            [
                NormalizedEventType.EARLY_WARNING,
                NormalizedEventType.ACTUAL_ALARM,
                NormalizedEventType.CLEAR,
            ],
        )


if __name__ == '__main__':
    unittest.main()
