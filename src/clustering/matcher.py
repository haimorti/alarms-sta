from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class MatchingPolicy:
    max_candidate_window_seconds: int
    minimum_overlap_ratio: float
    strong_subset_ratio: float


@dataclass(slots=True)
class MatchableEvent:
    normalized_event_id: int
    event_type: str
    started_at: datetime
    location_names: set[str]


@dataclass(slots=True)
class MatchResult:
    candidate_event_id: int | None
    method: str
    score: float
    explanation: str


class EventMatcher:
    def __init__(self, policy: MatchingPolicy) -> None:
        self.policy = policy

    def match_actual_alarm(
        self,
        early_warning: MatchableEvent,
        candidates: list[MatchableEvent],
    ) -> MatchResult:
        best_result = MatchResult(
            candidate_event_id=None,
            method="no_match",
            score=0.0,
            explanation="No candidate actual alarm met the minimum matching thresholds",
        )
        for candidate in candidates:
            result = self._score_candidate(early_warning, candidate)
            if result.score > best_result.score:
                best_result = result
        return best_result

    def _score_candidate(self, early_warning: MatchableEvent, candidate: MatchableEvent) -> MatchResult:
        if candidate.event_type != "actual_alarm":
            return MatchResult(
                candidate_event_id=candidate.normalized_event_id,
                method="event_type_incompatible",
                score=0.0,
                explanation="Candidate event is not an actual alarm",
            )

        time_gap_seconds = (candidate.started_at - early_warning.started_at).total_seconds()
        if time_gap_seconds < 0 or time_gap_seconds > self.policy.max_candidate_window_seconds:
            return MatchResult(
                candidate_event_id=candidate.normalized_event_id,
                method="time_window_rejected",
                score=0.0,
                explanation="Candidate event falls outside the configured time window",
            )

        overlap = len(early_warning.location_names & candidate.location_names)
        if not candidate.location_names:
            return MatchResult(
                candidate_event_id=candidate.normalized_event_id,
                method="empty_candidate_locations",
                score=0.0,
                explanation="Candidate event has no resolved locations",
            )

        overlap_ratio = overlap / max(len(candidate.location_names), 1)
        subset_ratio = overlap / max(len(early_warning.location_names), 1)
        if overlap_ratio < self.policy.minimum_overlap_ratio:
            return MatchResult(
                candidate_event_id=candidate.normalized_event_id,
                method="low_overlap",
                score=overlap_ratio,
                explanation="Spatial overlap is below the minimum configured overlap ratio",
            )

        time_score = max(0.0, 1 - (time_gap_seconds / self.policy.max_candidate_window_seconds))
        subset_bonus = 0.2 if subset_ratio >= self.policy.strong_subset_ratio else 0.0
        weighted_score = min(1.0, (0.45 * overlap_ratio) + (0.35 * subset_ratio) + (0.20 * time_score) + subset_bonus)
        explanation = (
            f"Matched by time proximity ({time_gap_seconds:.0f}s), overlap ratio ({overlap_ratio:.2f}), "
            f"and subset ratio ({subset_ratio:.2f})"
        )
        return MatchResult(
            candidate_event_id=candidate.normalized_event_id,
            method="time_overlap_subset",
            score=weighted_score,
            explanation=explanation,
        )


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
