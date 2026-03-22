from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.clustering.matcher import EventMatcher, MatchResult, MatchableEvent
from src.db.clusters import ClusterMemberInsert, EventClusterInsert, EventClusterRepository


@dataclass(slots=True)
class EventClusterResult:
    cluster_id: int | None
    match_result: MatchResult


class ClusteringService:
    def __init__(self, repository: EventClusterRepository, matcher: EventMatcher) -> None:
        self.repository = repository
        self.matcher = matcher

    def cluster_alarm_candidate(
        self,
        early_warning: MatchableEvent,
        candidates: list[MatchableEvent],
    ) -> EventClusterResult:
        match_result = self.matcher.match_actual_alarm(early_warning, candidates)
        if match_result.candidate_event_id is None or match_result.score <= 0:
            return EventClusterResult(cluster_id=None, match_result=match_result)

        candidate = next(candidate for candidate in candidates if candidate.normalized_event_id == match_result.candidate_event_id)
        cluster_id = self.repository.create_cluster(
            EventClusterInsert(
                trigger_event_id=early_warning.normalized_event_id,
                cluster_start_time=early_warning.started_at.isoformat(),
                cluster_end_time=max(early_warning.started_at, candidate.started_at).isoformat(),
                cluster_type="early_warning_to_actual_alarm",
                matching_method=match_result.method,
                confidence_score=match_result.score,
                explanation=match_result.explanation,
            )
        )
        self.repository.add_members(
            [
                ClusterMemberInsert(
                    cluster_id=cluster_id,
                    normalized_event_id=early_warning.normalized_event_id,
                    role_in_cluster="early_warning",
                    membership_score=1.0,
                    notes="Cluster trigger event",
                ),
                ClusterMemberInsert(
                    cluster_id=cluster_id,
                    normalized_event_id=candidate.normalized_event_id,
                    role_in_cluster="actual_alarm",
                    membership_score=match_result.score,
                    notes=match_result.explanation,
                ),
            ]
        )
        return EventClusterResult(cluster_id=cluster_id, match_result=match_result)
