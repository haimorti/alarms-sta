from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Final

SHARED_MEMORY_DB_URI: Final[str] = "file:alarms-sta?mode=memory&cache=shared"
_SHARED_MEMORY_KEEPALIVES: dict[str, sqlite3.Connection] = {}


def _coerce_database_path(database_path: str | Path) -> str:
    if isinstance(database_path, Path):
        return str(database_path)
    return database_path


def is_in_memory_database(database_path: str | Path) -> bool:
    value = _coerce_database_path(database_path)
    return value == ":memory:" or value.startswith("file:")


def connect_sqlite(database_path: str | Path) -> sqlite3.Connection:
    value = _coerce_database_path(database_path)
    return sqlite3.connect(value, uri=value.startswith("file:"))


def ensure_shared_memory_database(database_path: str | Path) -> None:
    value = _coerce_database_path(database_path)
    if not value.startswith("file:"):
        return
    if value not in _SHARED_MEMORY_KEEPALIVES:
        _SHARED_MEMORY_KEEPALIVES[value] = sqlite3.connect(value, uri=True)
