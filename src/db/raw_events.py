from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class RawEventInsert:
    fetched_at: datetime
    source_payload: Any
    source_url: str
    payload_hash: str
    source_event_id: str | None = None
    title: str | None = None
    category: str | None = None
    description: str | None = None
    http_status: int | None = None
    response_latency_ms: float | None = None
    archive_path: str | None = None
    parse_status: str = "pending"
    error_message: str | None = None


@dataclass(slots=True)
class RawEventRecord:
    id: int
    duplicate_of_raw_event_id: int | None
    is_duplicate: bool


class RawEventRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def save(self, event: RawEventInsert) -> RawEventRecord:
        source_payload = json.dumps(event.source_payload, ensure_ascii=False, separators=(",", ":"))
        with sqlite3.connect(self.database_path) as connection:
            duplicate_row = connection.execute(
                "SELECT id FROM raw_events WHERE payload_hash = ? ORDER BY id ASC LIMIT 1",
                (event.payload_hash,),
            ).fetchone()
            duplicate_of_raw_event_id = duplicate_row[0] if duplicate_row else None
            is_duplicate = duplicate_of_raw_event_id is not None
            cursor = connection.execute(
                """
                INSERT INTO raw_events (
                    fetched_at,
                    source_payload,
                    source_url,
                    source_event_id,
                    title,
                    cat,
                    desc,
                    payload_hash,
                    http_status,
                    response_latency_ms,
                    archive_path,
                    parse_status,
                    is_duplicate,
                    duplicate_of_raw_event_id,
                    error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.fetched_at.isoformat(),
                    source_payload,
                    event.source_url,
                    event.source_event_id,
                    event.title,
                    event.category,
                    event.description,
                    event.payload_hash,
                    event.http_status,
                    event.response_latency_ms,
                    event.archive_path,
                    event.parse_status,
                    int(is_duplicate),
                    duplicate_of_raw_event_id,
                    event.error_message,
                ),
            )
            connection.commit()
        return RawEventRecord(
            id=int(cursor.lastrowid),
            duplicate_of_raw_event_id=duplicate_of_raw_event_id,
            is_duplicate=is_duplicate,
        )
