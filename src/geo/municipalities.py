from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class MunicipalityGeometryRecord:
    name_he: str
    name_en: str | None
    polygon: str
    centroid_lat: float
    centroid_lon: float
    source_path: str
    source_dataset: str


@dataclass(slots=True)
class MunicipalityDatasetSummary:
    dataset_root: Path
    feature_count: int
    source_files: int
    aggregate_file: Path | None


class MunicipalityGeoJSONImporter:
    def __init__(self, dataset_root: Path) -> None:
        self.dataset_root = dataset_root

    def summarize(self) -> MunicipalityDatasetSummary:
        geojson_files = list(self._iter_candidate_geojson_files())
        feature_count = sum(1 for _ in self.iter_records())
        aggregate_file = self.dataset_root / 'municipalities.geojson'
        return MunicipalityDatasetSummary(
            dataset_root=self.dataset_root,
            feature_count=feature_count,
            source_files=len(geojson_files),
            aggregate_file=aggregate_file if aggregate_file.exists() else None,
        )

    def iter_records(self) -> list[MunicipalityGeometryRecord]:
        aggregate_path = self.dataset_root / 'municipalities.geojson'
        if aggregate_path.exists():
            return list(self._records_from_file(aggregate_path, source_dataset='israel-municipalities-polygons-master'))

        records: list[MunicipalityGeometryRecord] = []
        for path in self._iter_candidate_geojson_files():
            if path.name == 'municipalities.geojson':
                continue
            records.extend(self._records_from_file(path, source_dataset='israel-municipalities-polygons-master'))
        return records

    def _iter_candidate_geojson_files(self):
        for path in sorted(self.dataset_root.rglob('*.geojson')):
            if path.name == 'munis_osm_03072016.geojson':
                continue
            yield path

    def _records_from_file(self, path: Path, source_dataset: str):
        payload = json.loads(path.read_text(encoding='utf-8'))
        if payload.get('type') != 'FeatureCollection':
            raise ValueError(f'Unsupported GeoJSON type in {path}: {payload.get("type")}')
        for feature in payload.get('features', []):
            geometry = feature.get('geometry') or {}
            geometry_type = geometry.get('type')
            if geometry_type not in {'Polygon', 'MultiPolygon'}:
                continue
            properties = feature.get('properties') or {}
            name_he = self._pick_name(properties, ('MUN_HEB', 'name', 'name_he', 'hebrew_name'))
            if not name_he:
                continue
            name_en = self._pick_name(properties, ('MUN_ENG', 'name_en', 'english_name'))
            centroid_lon, centroid_lat = compute_geometry_centroid(geometry)
            yield MunicipalityGeometryRecord(
                name_he=name_he,
                name_en=name_en,
                polygon=json.dumps(geometry, ensure_ascii=False, separators=(',', ':')),
                centroid_lat=centroid_lat,
                centroid_lon=centroid_lon,
                source_path=str(path.relative_to(self.dataset_root.parent.parent)),
                source_dataset=source_dataset,
            )

    @staticmethod
    def _pick_name(properties: dict[str, Any], keys: tuple[str, ...]) -> str | None:
        for key in keys:
            value = properties.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None


def compute_geometry_centroid(geometry: dict[str, Any]) -> tuple[float, float]:
    geometry_type = geometry.get('type')
    coordinates = geometry.get('coordinates')
    if geometry_type == 'Polygon':
        return _polygon_centroid(coordinates)
    if geometry_type == 'MultiPolygon':
        best_centroid: tuple[float, float] | None = None
        best_area = -1.0
        for polygon in coordinates:
            centroid = _polygon_centroid(polygon)
            area = abs(_signed_ring_area(polygon[0])) if polygon else 0.0
            if area > best_area:
                best_area = area
                best_centroid = centroid
        if best_centroid is None:
            raise ValueError('MultiPolygon has no polygon coordinates')
        return best_centroid
    raise ValueError(f'Unsupported geometry type: {geometry_type}')


def _polygon_centroid(polygon_coordinates: list[Any]) -> tuple[float, float]:
    if not polygon_coordinates:
        raise ValueError('Polygon has no rings')
    outer_ring = polygon_coordinates[0]
    if len(outer_ring) < 3:
        raise ValueError('Polygon ring must contain at least three points')
    area = _signed_ring_area(outer_ring)
    if area == 0:
        return _average_point(outer_ring)

    cx = 0.0
    cy = 0.0
    for index in range(len(outer_ring) - 1):
        x0, y0 = outer_ring[index]
        x1, y1 = outer_ring[index + 1]
        cross = (x0 * y1) - (x1 * y0)
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    factor = 1 / (6 * area)
    return (cx * factor, cy * factor)


def _signed_ring_area(ring: list[list[float]]) -> float:
    total = 0.0
    normalized_ring = ring if ring[0] == ring[-1] else [*ring, ring[0]]
    for index in range(len(normalized_ring) - 1):
        x0, y0 = normalized_ring[index]
        x1, y1 = normalized_ring[index + 1]
        total += (x0 * y1) - (x1 * y0)
    return total / 2.0


def _average_point(ring: list[list[float]]) -> tuple[float, float]:
    xs = [point[0] for point in ring]
    ys = [point[1] for point in ring]
    return (sum(xs) / len(xs), sum(ys) / len(ys))
