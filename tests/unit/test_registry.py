from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.app.bootstrap import bootstrap_application
from src.config.settings import AppSettings
from src.geo.municipalities import MunicipalityGeoJSONImporter, compute_geometry_centroid


class MunicipalityImporterTest(unittest.TestCase):
    def test_primary_geojson_importer_reads_dataset_and_centroids(self) -> None:
        importer = MunicipalityGeoJSONImporter(Path('data/israel-municipalities-polygons-master'))

        summary = importer.summarize()
        records = importer.iter_records()
        abu_gosh = next(record for record in records if record.name_he == 'אבו גוש')

        self.assertGreater(summary.feature_count, 0)
        self.assertGreater(summary.source_files, 0)
        self.assertEqual(summary.aggregate_file, Path('data/israel-municipalities-polygons-master/municipalities.geojson'))
        self.assertTrue(abu_gosh.polygon.startswith('{"type":"Polygon"'))
        self.assertGreater(abu_gosh.centroid_lat, 0)
        self.assertGreater(abu_gosh.centroid_lon, 0)

    def test_compute_geometry_centroid_for_simple_polygon(self) -> None:
        lon, lat = compute_geometry_centroid(
            {
                'type': 'Polygon',
                'coordinates': [[[0, 0], [4, 0], [4, 2], [0, 2], [0, 0]]],
            }
        )

        self.assertAlmostEqual(lon, 2.0)
        self.assertAlmostEqual(lat, 1.0)


class SettlementRegistryTest(unittest.TestCase):
    def test_registry_resolves_exact_alias_and_normalized_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts = bootstrap_application(AppSettings.from_env(Path(tmp_dir)))

            exact = artifacts.settlement_registry.resolve_name('אבו גוש')
            alias = artifacts.settlement_registry.resolve_name('אבו-גוש')
            sub_area = artifacts.settlement_registry.resolve_name('נתניה-מזרח')
            farm = artifacts.settlement_registry.resolve_name('חוות יאיר')
            industrial = artifacts.settlement_registry.resolve_name('אזור-תעשייה בראון')
            unresolved = artifacts.settlement_registry.resolve_name('מקום לא קיים')

            self.assertEqual(exact.canonical_name, 'אבו גוש')
            self.assertEqual(exact.resolution_method, 'exact_name')
            self.assertEqual(alias.canonical_name, 'אבו גוש')
            self.assertIn(alias.resolution_method, {'generated_alias', 'manual_alias', 'manual_alias_normalized', 'normalized_name'})
            self.assertEqual(sub_area.canonical_name, 'נתניה - מזרח')
            self.assertEqual(farm.canonical_name, 'חוות יאיר')
            self.assertEqual(industrial.canonical_name, 'אזור תעשייה בראון')
            self.assertIsNotNone(farm.lat)
            self.assertIsNotNone(farm.lon)
            self.assertFalse(farm.has_direct_polygon)
            self.assertTrue(farm.fallback_geometry_used or not farm.has_direct_polygon)
            self.assertIsNone(unresolved.settlement_id)
            self.assertEqual(unresolved.resolution_method, 'unresolved')


if __name__ == '__main__':
    unittest.main()
