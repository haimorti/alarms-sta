from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class StringEnum(str, Enum):
    pass


class NormalizedEventType(StringEnum):
    UNKNOWN = "unknown"
    EARLY_WARNING = "early_warning"
    ACTUAL_ALARM = "actual_alarm"
    CLEAR = "clear"
    OTHER = "other"


class ProbabilityLabel(StringEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConfidenceLabel(StringEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(slots=True)
class RawEvent:
    fetched_at: datetime
    source_payload: dict[str, Any]
    source_event_id: str | None = None
    title: str | None = None
    category: str | None = None
    description: str | None = None
    payload_hash: str | None = None


@dataclass(slots=True)
class EventLocation:
    location_name_raw: str
    location_name_normalized: str | None = None
    settlement_id: int | None = None
    lat: float | None = None
    lon: float | None = None
    resolution_notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ScoreComponent:
    score_numeric: float
    score_label: ProbabilityLabel
    confidence_numeric: float
    confidence_label: ConfidenceLabel
    explanation: str


@dataclass(slots=True)
class ProbabilityBreakdown:
    spatial: ScoreComponent
    historical: ScoreComponent
    weighted: ScoreComponent


@dataclass(slots=True)
class NormalizedEvent:
    raw_event_id: int
    normalized_type: NormalizedEventType
    started_at: datetime | None = None
    ended_at: datetime | None = None
    source_event_id: str | None = None
    confidence_in_classification: float = 0.0
    notes: list[str] = field(default_factory=list)
    locations: list[EventLocation] = field(default_factory=list)
