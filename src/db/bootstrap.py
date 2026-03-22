from __future__ import annotations

import sqlite3
from pathlib import Path

from src.db.schema import SCHEMA_STATEMENTS
from src.db.sqlite import connect_sqlite, ensure_shared_memory_database


SETTLEMENT_COLUMN_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ('centroid_lat', 'ALTER TABLE settlements ADD COLUMN centroid_lat REAL'),
    ('centroid_lon', 'ALTER TABLE settlements ADD COLUMN centroid_lon REAL'),
    ('polygon', 'ALTER TABLE settlements ADD COLUMN polygon TEXT'),
    ('source_path', 'ALTER TABLE settlements ADD COLUMN source_path TEXT'),
)


def initialize_database(database_path: str | Path) -> None:
    ensure_shared_memory_database(database_path)
    with connect_sqlite(database_path) as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        _apply_lightweight_migrations(connection)
        connection.commit()


def _apply_lightweight_migrations(connection: sqlite3.Connection) -> None:
    columns = {row[1] for row in connection.execute("PRAGMA table_info(settlements)").fetchall()}
    for column_name, statement in SETTLEMENT_COLUMN_MIGRATIONS:
        if column_name not in columns:
            connection.execute(statement)
