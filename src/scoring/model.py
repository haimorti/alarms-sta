from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ScoringThresholds:
    low_threshold: int
    high_threshold: int


def build_scoring_thresholds(low_threshold: int, high_threshold: int) -> ScoringThresholds:
    if low_threshold >= high_threshold:
        raise ValueError("low_threshold must be smaller than high_threshold")
    return ScoringThresholds(low_threshold=low_threshold, high_threshold=high_threshold)
