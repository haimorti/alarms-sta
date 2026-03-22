from __future__ import annotations

from dataclasses import dataclass, field

from src.normalization.parser import ParsedAlertRecord
from src.types.domain import NormalizedEventType


EARLY_WARNING_KEYWORDS = ("מוקדמת", "צפויות להתקבל התרעות", "early warning", "preliminary")
ACTUAL_ALARM_KEYWORDS = (
    "ירי רקטות",
    "צבע אדום",
    "ירי טילים",
    "חדירת כלי טיס עוין",
    "חדירת מחבלים",
)
CLEAR_KEYWORDS = ("הסתיים", "סיום", "clear", "all clear")


@dataclass(slots=True)
class ClassificationResult:
    event_type: NormalizedEventType
    confidence: float
    reasons: list[str] = field(default_factory=list)


def classify_record(record: ParsedAlertRecord) -> ClassificationResult:
    haystacks = [text.lower() for text in (record.title, record.description, record.category) if text]
    reasons: list[str] = []

    if _matches_any(haystacks, EARLY_WARNING_KEYWORDS):
        reasons.append("Matched early-warning keywords in title/description/category")
        return ClassificationResult(
            event_type=NormalizedEventType.EARLY_WARNING,
            confidence=0.8,
            reasons=reasons,
        )

    if _matches_any(haystacks, CLEAR_KEYWORDS):
        reasons.append("Matched clear/end-of-event keywords in title/description/category")
        return ClassificationResult(
            event_type=NormalizedEventType.CLEAR,
            confidence=0.8,
            reasons=reasons,
        )

    if _matches_any(haystacks, ACTUAL_ALARM_KEYWORDS):
        reasons.append("Matched actual-alarm keywords in title/description/category")
        confidence = 0.75 if record.locations_raw else 0.6
        if record.locations_raw:
            reasons.append("Detected location list alongside alarm-style wording")
        return ClassificationResult(
            event_type=NormalizedEventType.ACTUAL_ALARM,
            confidence=confidence,
            reasons=reasons,
        )

    if record.locations_raw:
        reasons.append("Locations were extracted, but event type is still unknown")
        return ClassificationResult(
            event_type=NormalizedEventType.UNKNOWN,
            confidence=0.25,
            reasons=reasons,
        )

    reasons.append("No known classification pattern matched")
    return ClassificationResult(
        event_type=NormalizedEventType.UNKNOWN,
        confidence=0.1,
        reasons=reasons,
    )


def _matches_any(haystacks: list[str], keywords: tuple[str, ...]) -> bool:
    lowered_keywords = tuple(keyword.lower() for keyword in keywords)
    return any(keyword in haystack for haystack in haystacks for keyword in lowered_keywords)
