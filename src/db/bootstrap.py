from __future__ import annotations

import sqlite3
from pathlib import Path

from src.db.schema import SCHEMA_STATEMENTS


def initialize_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.commit()
