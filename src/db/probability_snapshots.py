from __future__ import annotations

import sqlite3

from src.db.sqlite import connect_sqlite
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ProbabilitySnapshotInsert:
    cluster_id: int
    settlement_id: int
    spatial_score: float
    spatial_label: str
    spatial_confidence: float
    spatial_confidence_label: str
    spatial_explanation: str
    historical_score: float
    historical_label: str
    historical_confidence: float
    historical_confidence_label: str
    historical_explanation: str
    weighted_score: float
    weighted_label: str
    weighted_confidence: float
    weighted_confidence_label: str
    weighted_explanation: str
    weighting_profile: str


class ProbabilitySnapshotRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def save(self, snapshot: ProbabilitySnapshotInsert) -> int:
        with connect_sqlite(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO probability_snapshots (
                    cluster_id,
                    settlement_id,
                    spatial_score,
                    spatial_label,
                    spatial_confidence,
                    spatial_confidence_label,
                    spatial_explanation,
                    historical_score,
                    historical_label,
                    historical_confidence,
                    historical_confidence_label,
                    historical_explanation,
                    weighted_score,
                    weighted_label,
                    weighted_confidence,
                    weighted_confidence_label,
                    weighted_explanation,
                    weighting_profile
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.cluster_id,
                    snapshot.settlement_id,
                    snapshot.spatial_score,
                    snapshot.spatial_label,
                    snapshot.spatial_confidence,
                    snapshot.spatial_confidence_label,
                    snapshot.spatial_explanation,
                    snapshot.historical_score,
                    snapshot.historical_label,
                    snapshot.historical_confidence,
                    snapshot.historical_confidence_label,
                    snapshot.historical_explanation,
                    snapshot.weighted_score,
                    snapshot.weighted_label,
                    snapshot.weighted_confidence,
                    snapshot.weighted_confidence_label,
                    snapshot.weighted_explanation,
                    snapshot.weighting_profile,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def history_for_settlement(self, settlement_id: int, limit: int = 20) -> list[dict[str, Any]]:
        with connect_sqlite(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT *
                FROM probability_snapshots
                WHERE settlement_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (settlement_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def latest_for_settlement_and_cluster(self, settlement_id: int, cluster_id: int) -> dict[str, Any] | None:
        with connect_sqlite(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT *
                FROM probability_snapshots
                WHERE settlement_id = ? AND cluster_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (settlement_id, cluster_id),
            ).fetchone()
        return dict(row) if row else None
