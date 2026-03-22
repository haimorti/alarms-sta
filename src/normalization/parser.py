from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass(slots=True)
class PrimaryMetadata:
    source_event_id: str | None = None
    title: str | None = None
    category: str | None = None
    description: str | None = None


@dataclass(slots=True)
class ParsedAlertRecord:
    source_event_id: str | None
    title: str | None
    category: str | None
    description: str | None
    locations_raw: list[str]
    notes: list[str] = field(default_factory=list)


LOCATION_KEYS = ("cities", "data", "locations", "areaNames", "settlements")
ID_KEYS = ("id", "alertId", "eventId")
TITLE_KEYS = ("title", "name")
CATEGORY_KEYS = ("cat", "category", "threat")
DESCRIPTION_KEYS = ("desc", "description", "text")


def extract_primary_metadata(payload: Any) -> PrimaryMetadata:
    record = _coerce_records(payload)[0] if _coerce_records(payload) else {}
    if not isinstance(record, dict):
        return PrimaryMetadata()
    return PrimaryMetadata(
        source_event_id=_first_text(record, ID_KEYS),
        title=_first_text(record, TITLE_KEYS),
        category=_first_text(record, CATEGORY_KEYS),
        description=_first_text(record, DESCRIPTION_KEYS),
    )


def parse_alert_payload(payload: Any) -> list[ParsedAlertRecord]:
    parsed_records: list[ParsedAlertRecord] = []
    for candidate in _coerce_records(payload):
        if not isinstance(candidate, dict):
            continue
        notes: list[str] = []
        locations = _extract_locations(candidate, notes)
        parsed_records.append(
            ParsedAlertRecord(
                source_event_id=_first_text(candidate, ID_KEYS),
                title=_first_text(candidate, TITLE_KEYS),
                category=_first_text(candidate, CATEGORY_KEYS),
                description=_first_text(candidate, DESCRIPTION_KEYS),
                locations_raw=locations,
                notes=notes,
            )
        )
    return parsed_records


def _coerce_records(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "alerts", "items"):
            value = payload.get(key)
            if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
                return value
        return [payload]
    return []


def _extract_locations(record: dict[str, Any], notes: list[str]) -> list[str]:
    for key in LOCATION_KEYS:
        value = record.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            return _split_locations(value)
        if isinstance(value, list):
            extracted = _flatten_location_values(value)
            if extracted:
                return extracted
            notes.append(f"Could not confidently extract locations from list key '{key}'")
    notes.append("No location list could be extracted from known keys")
    return []


def _flatten_location_values(values: Iterable[Any]) -> list[str]:
    results: list[str] = []
    for value in values:
        if isinstance(value, str):
            results.extend(_split_locations(value))
        elif isinstance(value, dict):
            for key in ("label", "name", "value", "city"):
                text = value.get(key)
                if isinstance(text, str):
                    results.extend(_split_locations(text))
                    break
    return [value for value in dict.fromkeys(results) if value]


def _split_locations(value: str) -> list[str]:
    separators = [",", "|", "\n", ";"]
    chunks = [value]
    for separator in separators:
        next_chunks: list[str] = []
        for chunk in chunks:
            next_chunks.extend(chunk.split(separator))
        chunks = next_chunks
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def _first_text(record: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = record.get(key)
        if value is None:
            continue
        if isinstance(value, (str, int, float)):
            return str(value)
    return None
