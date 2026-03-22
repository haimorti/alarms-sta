from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.app.bootstrap import bootstrap_application
from src.config.settings import AppSettings
from src.scoring.engine import SettlementEventContext


class ProbabilityEngineTest(unittest.TestCase):
    def test_evaluate_returns_separate_breakdown_components(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts = bootstrap_application(AppSettings.from_env(Path(tmp_dir)))
            context = SettlementEventContext(
                cluster_id=1,
                settlement_id=10,
                settlement_name="רמת גן",
                settlement_lat=32.08,
                settlement_lon=34.81,
                event_locations=[
                    {"lat": 32.08, "lon": 34.81},
                    {"lat": 32.09, "lon": 34.80},
                    {"lat": 32.07, "lon": 34.82},
                ],
                cluster_match_confidence=0.8,
            )

            breakdown = artifacts.probability_engine.evaluate(context)

            self.assertGreaterEqual(breakdown.spatial.score_numeric, 0)
            self.assertLessEqual(breakdown.spatial.score_numeric, 100)
            self.assertGreaterEqual(breakdown.weighted.score_numeric, 0)
            self.assertLessEqual(breakdown.weighted.score_numeric, 100)
            self.assertIn("Weighted score combines spatial", breakdown.weighted.explanation)


if __name__ == "__main__":
    unittest.main()
