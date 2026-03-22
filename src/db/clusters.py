from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class EventClusterInsert:
    trigger_event_id: int
    cluster_start_time: str | None
    cluster_end_time: str | None
    cluster_type: str
    matching_method: str
    confidence_score: float
    explanation: str


@dataclass(slots=True)
class ClusterMemberInsert:
    cluster_id: int
    normalized_event_id: int
    role_in_cluster: str
    membership_score: float
    notes: str | None


class EventClusterRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def create_cluster(self, cluster: EventClusterInsert) -> int:
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO event_clusters (
                    trigger_event_id,
                    cluster_start_time,
                    cluster_end_time,
                    cluster_type,
                    matching_method,
                    confidence_score,
                    explanation
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cluster.trigger_event_id,
                    cluster.cluster_start_time,
                    cluster.cluster_end_time,
                    cluster.cluster_type,
                    cluster.matching_method,
                    cluster.confidence_score,
                    cluster.explanation,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def add_members(self, members: list[ClusterMemberInsert]) -> None:
        if not members:
            return
        with sqlite3.connect(self.database_path) as connection:
            connection.executemany(
                """
                INSERT INTO cluster_members (
                    cluster_id,
                    normalized_event_id,
                    role_in_cluster,
                    membership_score,
                    notes
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        member.cluster_id,
                        member.normalized_event_id,
                        member.role_in_cluster,
                        member.membership_score,
                        member.notes,
                    )
                    for member in members
                ],
            )
            connection.commit()
