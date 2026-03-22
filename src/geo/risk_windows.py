from __future__ import annotations

from dataclasses import dataclass

from src.db.risk_windows import RiskWindowInsert, RiskWindowRepository


@dataclass(slots=True)
class RiskWindowDraft:
    cluster_id: int
    normalized_event_id: int | None
    phase_index: int
    phase_label: str
    window_started_at: str
    window_ended_at: str | None
    geometry_kind: str
    geometry_payload: str
    centroid_lat: float | None
    centroid_lon: float | None
    area_scale: float | None
    trajectory_confidence: float
    notes: str | None


class RiskWindowService:
    def __init__(self, repository: RiskWindowRepository) -> None:
        self.repository = repository

    def record_window(self, draft: RiskWindowDraft) -> int:
        return self.repository.save(
            RiskWindowInsert(
                cluster_id=draft.cluster_id,
                normalized_event_id=draft.normalized_event_id,
                phase_index=draft.phase_index,
                phase_label=draft.phase_label,
                window_started_at=draft.window_started_at,
                window_ended_at=draft.window_ended_at,
                geometry_kind=draft.geometry_kind,
                geometry_payload=draft.geometry_payload,
                centroid_lat=draft.centroid_lat,
                centroid_lon=draft.centroid_lon,
                area_scale=draft.area_scale,
                trajectory_confidence=draft.trajectory_confidence,
                notes=draft.notes,
            )
        )

    def latest_window(self, cluster_id: int) -> dict | None:
        return self.repository.latest_for_cluster(cluster_id)
