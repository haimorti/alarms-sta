from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MatchingPolicy:
    max_candidate_window_seconds: int
    minimum_overlap_ratio: float
    strong_subset_ratio: float


def build_matching_policy(
    max_candidate_window_seconds: int,
    minimum_overlap_ratio: float,
    strong_subset_ratio: float,
) -> MatchingPolicy:
    return MatchingPolicy(
        max_candidate_window_seconds=max_candidate_window_seconds,
        minimum_overlap_ratio=minimum_overlap_ratio,
        strong_subset_ratio=strong_subset_ratio,
    )
