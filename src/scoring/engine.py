from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from src.config.settings import ScoringConfig
from src.db.probability_snapshots import ProbabilitySnapshotInsert, ProbabilitySnapshotRepository
from src.types.domain import ConfidenceLabel, ProbabilityBreakdown, ProbabilityLabel, ScoreComponent


@dataclass(slots=True)
class SettlementEventContext:
    cluster_id: int
    settlement_id: int
    settlement_name: str
    settlement_lat: float | None
    settlement_lon: float | None
    event_locations: list[dict[str, object]]
    cluster_match_confidence: float


class ProbabilityEngineV1:
    def __init__(self, database_path: Path, scoring_config: ScoringConfig) -> None:
        self.database_path = database_path
        self.scoring_config = scoring_config
        self.snapshot_repository = ProbabilitySnapshotRepository(database_path)

    def evaluate(self, context: SettlementEventContext) -> ProbabilityBreakdown:
        spatial = self._build_spatial_component(context)
        historical = self._build_historical_component(context)
        weighted_score = (
            self.scoring_config.spatial_weight * spatial.score_numeric
            + self.scoring_config.historical_weight * historical.score_numeric
        )
        weighted_confidence = min(
            1.0,
            (self.scoring_config.spatial_weight * spatial.confidence_numeric)
            + (self.scoring_config.historical_weight * historical.confidence_numeric)
            + (0.15 * context.cluster_match_confidence),
        )
        weighted = ScoreComponent(
            score_numeric=round(weighted_score, 2),
            score_label=self._score_label(weighted_score),
            confidence_numeric=round(weighted_confidence, 2),
            confidence_label=self._confidence_label(weighted_confidence),
            explanation=(
                f"Weighted score combines spatial ({self.scoring_config.spatial_weight:.2f}) and historical "
                f"({self.scoring_config.historical_weight:.2f}) components, adjusted by cluster confidence"
            ),
        )
        return ProbabilityBreakdown(spatial=spatial, historical=historical, weighted=weighted)

    def evaluate_and_persist(self, context: SettlementEventContext) -> int:
        breakdown = self.evaluate(context)
        return self.snapshot_repository.save(
            ProbabilitySnapshotInsert(
                cluster_id=context.cluster_id,
                settlement_id=context.settlement_id,
                spatial_score=breakdown.spatial.score_numeric,
                spatial_label=breakdown.spatial.score_label.value,
                spatial_confidence=breakdown.spatial.confidence_numeric,
                spatial_confidence_label=breakdown.spatial.confidence_label.value,
                spatial_explanation=breakdown.spatial.explanation,
                historical_score=breakdown.historical.score_numeric,
                historical_label=breakdown.historical.score_label.value,
                historical_confidence=breakdown.historical.confidence_numeric,
                historical_confidence_label=breakdown.historical.confidence_label.value,
                historical_explanation=breakdown.historical.explanation,
                weighted_score=breakdown.weighted.score_numeric,
                weighted_label=breakdown.weighted.score_label.value,
                weighted_confidence=breakdown.weighted.confidence_numeric,
                weighted_confidence_label=breakdown.weighted.confidence_label.value,
                weighted_explanation=breakdown.weighted.explanation,
                weighting_profile=json.dumps(
                    {
                        "spatial_weight": self.scoring_config.spatial_weight,
                        "historical_weight": self.scoring_config.historical_weight,
                    }
                ),
            )
        )

    def _build_spatial_component(self, context: SettlementEventContext) -> ScoreComponent:
        coords = [
            (float(loc["lat"]), float(loc["lon"]))
            for loc in context.event_locations
            if loc.get("lat") is not None and loc.get("lon") is not None
        ]
        if not coords or context.settlement_lat is None or context.settlement_lon is None:
            return ScoreComponent(
                score_numeric=50.0,
                score_label=self._score_label(50),
                confidence_numeric=0.2,
                confidence_label=self._confidence_label(0.2),
                explanation="Not enough coordinate coverage to derive a strong spatial estimate",
            )

        centroid_lat = sum(lat for lat, _ in coords) / len(coords)
        centroid_lon = sum(lon for _, lon in coords) / len(coords)
        distances = [self._distance(centroid_lat, centroid_lon, lat, lon) for lat, lon in coords]
        target_distance = self._distance(centroid_lat, centroid_lon, context.settlement_lat, context.settlement_lon)
        max_distance = max(max(distances), target_distance, 0.0001)
        centrality = max(0.0, 1 - (target_distance / max_distance))

        nearest_distances = sorted(
            self._distance(context.settlement_lat, context.settlement_lon, lat, lon)
            for lat, lon in coords
            if (lat, lon) != (context.settlement_lat, context.settlement_lon)
        )
        density = 1.0 if not nearest_distances else max(0.0, 1 - (sum(nearest_distances[:3]) / max(len(nearest_distances[:3]), 1) / max_distance))
        edge_score = centrality
        spatial_score = (0.45 * centrality + 0.35 * edge_score + 0.20 * density) * 100
        confidence = min(1.0, 0.3 + (0.05 * len(coords)))
        return ScoreComponent(
            score_numeric=round(spatial_score, 2),
            score_label=self._score_label(spatial_score),
            confidence_numeric=round(confidence, 2),
            confidence_label=self._confidence_label(confidence),
            explanation=(
                f"Spatial score is based on centroid centrality, edge distance proxy, and local settlement density "
                f"within an event of {len(coords)} mapped locations"
            ),
        )

    def _build_historical_component(self, context: SettlementEventContext) -> ScoreComponent:
        with sqlite3.connect(self.database_path) as connection:
            total_early_warnings = connection.execute(
                """
                SELECT COUNT(DISTINCT ne.id)
                FROM normalized_events ne
                JOIN event_locations el ON el.normalized_event_id = ne.id
                WHERE ne.normalized_type = 'early_warning'
                  AND el.settlement_id = ?
                """,
                (context.settlement_id,),
            ).fetchone()[0]
            matched_transitions = connection.execute(
                """
                SELECT COUNT(DISTINCT ew.normalized_event_id)
                FROM cluster_members ew
                JOIN cluster_members aa ON aa.cluster_id = ew.cluster_id
                JOIN event_locations ael ON ael.normalized_event_id = aa.normalized_event_id
                WHERE ew.role_in_cluster = 'early_warning'
                  AND aa.role_in_cluster = 'actual_alarm'
                  AND ael.settlement_id = ?
                """,
                (context.settlement_id,),
            ).fetchone()[0]

        if total_early_warnings == 0:
            return ScoreComponent(
                score_numeric=50.0,
                score_label=self._score_label(50),
                confidence_numeric=0.15,
                confidence_label=self._confidence_label(0.15),
                explanation="No historical early-warning sample exists yet for this settlement, so the estimate remains neutral",
            )

        transition_rate = matched_transitions / total_early_warnings
        sample_quality = min(1.0, total_early_warnings / 10)
        historical_score = transition_rate * 100
        confidence = 0.2 + (0.7 * sample_quality)
        return ScoreComponent(
            score_numeric=round(historical_score, 2),
            score_label=self._score_label(historical_score),
            confidence_numeric=round(confidence, 2),
            confidence_label=self._confidence_label(confidence),
            explanation=(
                f"Historical score is based on {matched_transitions} matched transitions out of "
                f"{total_early_warnings} historical early-warning observations"
            ),
        )

    def _score_label(self, score: float) -> ProbabilityLabel:
        if score <= self.scoring_config.low_threshold:
            return ProbabilityLabel.LOW
        if score <= self.scoring_config.high_threshold:
            return ProbabilityLabel.MEDIUM
        return ProbabilityLabel.HIGH

    @staticmethod
    def _confidence_label(confidence: float) -> ConfidenceLabel:
        if confidence < 0.34:
            return ConfidenceLabel.LOW
        if confidence < 0.67:
            return ConfidenceLabel.MEDIUM
        return ConfidenceLabel.HIGH

    @staticmethod
    def _distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)
