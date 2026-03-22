from __future__ import annotations

import json
from dataclasses import dataclass

from src.db.normalized_events import EventLocationInsert, NormalizedEventInsert, NormalizedEventRepository
from src.db.raw_events import RawEventRepository
from src.geo.registry import SettlementRegistryService, SettlementResolution
from src.normalization.classifier import ClassificationResult, classify_record
from src.normalization.parser import ParsedAlertRecord, parse_alert_payload


@dataclass(slots=True)
class NormalizedRecordPreview:
    parsed_record: ParsedAlertRecord
    classification: ClassificationResult
    resolved_locations: list[SettlementResolution]


@dataclass(slots=True)
class PersistedNormalizationResult:
    normalized_event_ids: list[int]
    unresolved_names: list[str]


class NormalizationService:
    def __init__(
        self,
        raw_event_repository: RawEventRepository,
        normalized_event_repository: NormalizedEventRepository,
        settlement_registry: SettlementRegistryService,
    ) -> None:
        self.raw_event_repository = raw_event_repository
        self.normalized_event_repository = normalized_event_repository
        self.settlement_registry = settlement_registry

    def normalize_payload(self, payload: object) -> list[NormalizedRecordPreview]:
        previews: list[NormalizedRecordPreview] = []
        for parsed_record in parse_alert_payload(payload):
            classification = classify_record(parsed_record)
            resolved_locations = [self.settlement_registry.resolve_name(name) for name in parsed_record.locations_raw]
            previews.append(
                NormalizedRecordPreview(
                    parsed_record=parsed_record,
                    classification=classification,
                    resolved_locations=resolved_locations,
                )
            )
        return previews

    def normalize_raw_event(self, raw_event_id: int) -> PersistedNormalizationResult:
        payload = self.raw_event_repository.get_payload(raw_event_id)
        fetched_at = self.raw_event_repository.get_fetched_at(raw_event_id)
        previews = self.normalize_payload(payload)
        normalized_event_ids: list[int] = []
        unresolved_names: list[str] = []

        try:
            for preview in previews:
                notes = list(preview.parsed_record.notes) + preview.classification.reasons
                normalized_event_id = self.normalized_event_repository.save_event(
                    NormalizedEventInsert(
                        raw_event_id=raw_event_id,
                        normalized_type=preview.classification.event_type.value,
                        started_at=fetched_at,
                        ended_at=None,
                        source_event_id=preview.parsed_record.source_event_id,
                        confidence_in_classification=preview.classification.confidence,
                        notes=json.dumps(notes, ensure_ascii=False),
                    )
                )
                normalized_event_ids.append(normalized_event_id)
                location_inserts: list[EventLocationInsert] = []
                for location in preview.resolved_locations:
                    if location.settlement_id is None:
                        unresolved_names.append(location.raw_name)
                    location_inserts.append(
                        EventLocationInsert(
                            normalized_event_id=normalized_event_id,
                            location_name_raw=location.raw_name,
                            location_name_normalized=location.canonical_name,
                            settlement_id=location.settlement_id,
                            lat=location.lat,
                            lon=location.lon,
                            resolution_confidence=location.resolution_confidence,
                            resolution_notes=location.resolution_method,
                        )
                    )
                self.normalized_event_repository.save_locations(location_inserts)
            self.raw_event_repository.update_parse_status(raw_event_id, "parsed")
        except Exception as exc:
            self.raw_event_repository.update_parse_status(raw_event_id, "failed", str(exc))
            raise

        return PersistedNormalizationResult(
            normalized_event_ids=normalized_event_ids,
            unresolved_names=sorted(set(unresolved_names)),
        )
