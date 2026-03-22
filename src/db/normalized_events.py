from __future__ import annotations

import sqlite3

from src.db.sqlite import connect_sqlite
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class NormalizedEventInsert:
    raw_event_id: int
    normalized_type: str
    started_at: str | None
    ended_at: str | None
    source_event_id: str | None
    confidence_in_classification: float
    notes: str | None


@dataclass(slots=True)
class EventLocationInsert:
    normalized_event_id: int
    location_name_raw: str
    location_name_normalized: str | None
    settlement_id: int | None
    lat: float | None
    lon: float | None
    resolution_confidence: float
    resolution_notes: str | None


class NormalizedEventRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def save_event(self, event: NormalizedEventInsert) -> int:
        with connect_sqlite(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO normalized_events (
                    raw_event_id,
                    normalized_type,
                    started_at,
                    ended_at,
                    source_event_id,
                    confidence_in_classification,
                    notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.raw_event_id,
                    event.normalized_type,
                    event.started_at,
                    event.ended_at,
                    event.source_event_id,
                    event.confidence_in_classification,
                    event.notes,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def save_locations(self, locations: list[EventLocationInsert]) -> None:
        if not locations:
            return
        with connect_sqlite(self.database_path) as connection:
            connection.executemany(
                """
                INSERT INTO event_locations (
                    normalized_event_id,
                    location_name_raw,
                    location_name_normalized,
                    settlement_id,
                    lat,
                    lon,
                    resolution_confidence,
                    resolution_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        location.normalized_event_id,
                        location.location_name_raw,
                        location.location_name_normalized,
                        location.settlement_id,
                        location.lat,
                        location.lon,
                        location.resolution_confidence,
                        location.resolution_notes,
                    )
                    for location in locations
                ],
            )
            connection.commit()
