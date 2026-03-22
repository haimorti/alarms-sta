from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.app.bootstrap import bootstrap_application
from src.config.settings import AppSettings


class SettlementRegistryTest(unittest.TestCase):
    def test_registry_resolves_exact_and_alias_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts = bootstrap_application(AppSettings.from_env(Path(tmp_dir)))

            exact = artifacts.settlement_registry.resolve_name("אבו גוש")
            alias = artifacts.settlement_registry.resolve_name("אבו-גוש")
            unresolved = artifacts.settlement_registry.resolve_name("מקום לא קיים")

            self.assertEqual(exact.canonical_name, "אבו גוש")
            self.assertEqual(exact.resolution_method, "exact_name")
            self.assertEqual(alias.canonical_name, "אבו גוש")
            self.assertEqual(alias.resolution_method, "manual_alias")
            self.assertIsNone(unresolved.settlement_id)
            self.assertEqual(unresolved.resolution_method, "unresolved")


if __name__ == "__main__":
    unittest.main()
