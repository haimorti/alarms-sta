from __future__ import annotations

from dataclasses import dataclass

from src.types.domain import NormalizedEventType


@dataclass(slots=True)
class ClassificationRule:
    name: str
    description: str
    event_type: NormalizedEventType


DEFAULT_CLASSIFICATION_RULES: tuple[ClassificationRule, ...] = (
    ClassificationRule(
        name="placeholder-unknown",
        description="Stage 1 placeholder until live payload patterns are documented.",
        event_type=NormalizedEventType.UNKNOWN,
    ),
)
