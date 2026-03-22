from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from src.db.settlements import SettlementAliasSeed, SettlementRepository, SettlementSeed


@dataclass(slots=True)
class RegistrySource:
    path: Path
    purpose: str


@dataclass(slots=True)
class SettlementResolution:
    raw_name: str
    settlement_id: int | None
    canonical_name: str | None
    resolution_confidence: float
    resolution_method: str
    lat: float | None
    lon: float | None


@dataclass(slots=True)
class SeedImportResult:
    settlements_imported: int
    aliases_imported: int


@dataclass(slots=True)
class UnresolvedLocation:
    raw_name: str
    reason: str


REGISTRY_SOURCES: tuple[RegistrySource, ...] = (
    RegistrySource(Path("data/coord.csv"), "Primary settlement coordinates seed"),
    RegistrySource(Path("data/location_dictionary.csv"), "Hebrew/English settlement name dictionary"),
    RegistrySource(Path("data/coord_area.csv"), "Known area/polygon fragments for settlements and sublocations"),
    RegistrySource(Path("data/missing_cities.json"), "Alias and unresolved-location normalization hints"),
)


class SettlementRegistryService:
    def __init__(self, project_root: Path, repository: SettlementRepository) -> None:
        self.project_root = project_root
        self.repository = repository

    def import_seed_data(self) -> SeedImportResult:
        coord_rows = self._read_csv(self.project_root / "data" / "coord.csv")
        english_rows = self._read_csv(self.project_root / "data" / "location_dictionary.csv")
        geometry_rows = self._read_csv(self.project_root / "data" / "coord_area.csv")
        alias_map = self._read_json(self.project_root / "data" / "missing_cities.json")

        english_by_he = {row["Hebrew"].strip(): row["English"].strip() for row in english_rows if row.get("Hebrew")}
        geometry_by_name = {row["loc"].strip(): row["points"].strip() for row in geometry_rows if row.get("loc")}

        settlement_seeds: list[SettlementSeed] = []
        alias_seeds: list[SettlementAliasSeed] = []
        for row in coord_rows:
            raw_name = (row.get("loc") or "").strip()
            if not raw_name:
                continue
            canonical_name = alias_map.get(raw_name, raw_name).strip() if raw_name in alias_map else raw_name
            name_he = canonical_name or raw_name
            settlement_seeds.append(
                SettlementSeed(
                    name_he=name_he,
                    name_en=english_by_he.get(name_he) or english_by_he.get(raw_name),
                    lat=self._maybe_float(row.get("lat")),
                    lon=self._maybe_float(row.get("long")),
                    geometry=geometry_by_name.get(name_he) or geometry_by_name.get(raw_name),
                    source_dataset="coord.csv",
                )
            )
        settlement_ids = self.repository.bulk_upsert_settlements(settlement_seeds)
        settlements_imported = len(settlement_seeds)

        for settlement_seed in settlement_seeds:
            alias_seeds.append(
                SettlementAliasSeed(
                    settlement_id=settlement_ids.get(settlement_seed.name_he),
                    alias=settlement_seed.name_he,
                    alias_type="canonical_name",
                    confidence=1.0,
                    notes="Imported from coord.csv",
                )
            )

        for raw_alias, canonical_name in alias_map.items():
            canonical_name = canonical_name.strip()
            settlement_id = None
            confidence = 0.4
            alias_type = "known_missing"
            if canonical_name:
                settlement_id = settlement_ids.get(canonical_name)
                confidence = 0.9 if settlement_id else 0.5
                alias_type = "manual_alias"
            alias_seeds.append(
                SettlementAliasSeed(
                    settlement_id=settlement_id,
                    alias=raw_alias,
                    alias_type=alias_type,
                    confidence=confidence,
                    notes="Imported from missing_cities.json",
                )
            )
        self.repository.bulk_upsert_aliases(alias_seeds)
        aliases_imported = len(alias_seeds)

        return SeedImportResult(
            settlements_imported=settlements_imported,
            aliases_imported=aliases_imported,
        )

    def resolve_name(self, raw_name: str) -> SettlementResolution:
        settlement_id, canonical_name, confidence, method, lat, lon = self.repository.find_by_name_or_alias(raw_name.strip())
        if settlement_id is None:
            return SettlementResolution(
                raw_name=raw_name,
                settlement_id=None,
                canonical_name=None,
                resolution_confidence=0.0,
                resolution_method="unresolved",
                lat=None,
                lon=None,
            )
        return SettlementResolution(
            raw_name=raw_name,
            settlement_id=int(settlement_id),
            canonical_name=canonical_name,
            resolution_confidence=float(confidence),
            resolution_method=method or "alias",
            lat=lat,
            lon=lon,
        )

    def build_unresolved_report(self, raw_names: list[str]) -> list[UnresolvedLocation]:
        report: list[UnresolvedLocation] = []
        for name in raw_names:
            resolution = self.resolve_name(name)
            if resolution.settlement_id is None:
                report.append(UnresolvedLocation(raw_name=name, reason="No canonical settlement or alias match"))
        return report

    @staticmethod
    def _read_csv(path: Path) -> list[dict[str, str]]:
        with path.open(encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    @staticmethod
    def _read_json(path: Path) -> dict[str, str]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _maybe_float(value: str | None) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except ValueError:
            return None
