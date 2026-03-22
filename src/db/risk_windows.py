from __future__ import annotations

import sqlite3

from src.db.sqlite import connect_sqlite
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class RiskWindowInsert:
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


class RiskWindowRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def save(self, risk_window: RiskWindowInsert) -> int:
        with connect_sqlite(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO risk_windows (
                    cluster_id,
                    normalized_event_id,
                    phase_index,
                    phase_label,
                    window_started_at,
                    window_ended_at,
                    geometry_kind,
                    geometry_payload,
                    centroid_lat,
                    centroid_lon,
                    area_scale,
                    trajectory_confidence,
                    notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    risk_window.cluster_id,
                    risk_window.normalized_event_id,
                    risk_window.phase_index,
                    risk_window.phase_label,
                    risk_window.window_started_at,
                    risk_window.window_ended_at,
                    risk_window.geometry_kind,
                    risk_window.geometry_payload,
                    risk_window.centroid_lat,
                    risk_window.centroid_lon,
                    risk_window.area_scale,
                    risk_window.trajectory_confidence,
                    risk_window.notes,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def latest_for_cluster(self, cluster_id: int) -> dict[str, Any] | None:
        with connect_sqlite(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT * FROM risk_windows
                WHERE cluster_id = ?
                ORDER BY phase_index DESC, window_started_at DESC, id DESC
                LIMIT 1
                """,
                (cluster_id,),
            ).fetchone()
        return dict(row) if row else None
