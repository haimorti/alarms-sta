from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.geo.alias_resolver import AliasResolver, ResolvedLocation
from src.normalization.classifier import ClassificationResult, classify_record
from src.normalization.parser import ParsedAlertRecord, parse_alert_payload


@dataclass(slots=True)
class NormalizedRecordPreview:
    parsed_record: ParsedAlertRecord
    classification: ClassificationResult
    resolved_locations: list[ResolvedLocation]


class NormalizationService:
    def __init__(self, alias_file: Path) -> None:
        self.alias_resolver = AliasResolver.from_json(alias_file)

    def normalize_payload(self, payload: object) -> list[NormalizedRecordPreview]:
        previews: list[NormalizedRecordPreview] = []
        for parsed_record in parse_alert_payload(payload):
            classification = classify_record(parsed_record)
            resolved_locations = [self.alias_resolver.resolve(name) for name in parsed_record.locations_raw]
            previews.append(
                NormalizedRecordPreview(
                    parsed_record=parsed_record,
                    classification=classification,
                    resolved_locations=resolved_locations,
                )
            )
        return previews
