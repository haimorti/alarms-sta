from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SettlementSeed:
    name_he: str
    name_en: str | None
    lat: float | None
    lon: float | None
    centroid_lat: float | None
    centroid_lon: float | None
    polygon: str | None
    geometry: str | None
    source_dataset: str
    source_path: str | None = None


@dataclass(slots=True)
class SettlementAliasSeed:
    settlement_id: int | None
    alias: str
    alias_type: str
    confidence: float
    notes: str | None


class SettlementRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def upsert_settlement(self, settlement: SettlementSeed) -> int:
        with sqlite3.connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT id FROM settlements WHERE name_he = ?",
                (settlement.name_he,),
            ).fetchone()
            if row:
                connection.execute(
                    """
                    UPDATE settlements
                    SET name_en = COALESCE(?, name_en),
                        lat = COALESCE(?, lat),
                        lon = COALESCE(?, lon),
                        centroid_lat = COALESCE(?, centroid_lat),
                        centroid_lon = COALESCE(?, centroid_lon),
                        polygon = COALESCE(?, polygon),
                        geometry = COALESCE(?, geometry),
                        source_dataset = ?,
                        source_path = COALESCE(?, source_path)
                    WHERE id = ?
                    """,
                    (
                        settlement.name_en,
                        settlement.lat,
                        settlement.lon,
                        settlement.centroid_lat,
                        settlement.centroid_lon,
                        settlement.polygon,
                        settlement.geometry,
                        settlement.source_dataset,
                        settlement.source_path,
                        row[0],
                    ),
                )
                connection.commit()
                return int(row[0])

            cursor = connection.execute(
                """
                INSERT INTO settlements (name_he, name_en, lat, lon, centroid_lat, centroid_lon, polygon, geometry, source_dataset, source_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    settlement.name_he,
                    settlement.name_en,
                    settlement.lat,
                    settlement.lon,
                    settlement.centroid_lat,
                    settlement.centroid_lon,
                    settlement.polygon,
                    settlement.geometry,
                    settlement.source_dataset,
                    settlement.source_path,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def upsert_alias(self, alias: SettlementAliasSeed) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO settlement_aliases (settlement_id, alias, alias_type, confidence, notes)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(alias) DO UPDATE SET
                    settlement_id = excluded.settlement_id,
                    alias_type = excluded.alias_type,
                    confidence = excluded.confidence,
                    notes = excluded.notes
                """,
                (
                    alias.settlement_id,
                    alias.alias,
                    alias.alias_type,
                    alias.confidence,
                    alias.notes,
                ),
            )
            connection.commit()

    def find_by_name_or_alias(self, raw_name: str) -> tuple[int | None, str | None, float, str | None, float | None, float | None]:
        with sqlite3.connect(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT s.id, s.name_he, 1.0 as confidence, 'exact_name' as method, COALESCE(s.centroid_lat, s.lat), COALESCE(s.centroid_lon, s.lon)
                FROM settlements s
                WHERE s.name_he = ?
                UNION ALL
                SELECT s.id, s.name_he, sa.confidence, sa.alias_type, COALESCE(s.centroid_lat, s.lat), COALESCE(s.centroid_lon, s.lon)
                FROM settlement_aliases sa
                LEFT JOIN settlements s ON s.id = sa.settlement_id
                WHERE sa.alias = ?
                LIMIT 1
                """,
                (raw_name, raw_name),
            ).fetchone()
        if not row:
            return (None, None, 0.0, None, None, None)
        return row

    def bulk_upsert_settlements(self, settlements: list[SettlementSeed]) -> dict[str, int]:
        with sqlite3.connect(self.database_path) as connection:
            existing_rows = connection.execute("SELECT id, name_he FROM settlements").fetchall()
            existing_by_name = {name_he: settlement_id for settlement_id, name_he in existing_rows}
            for settlement in settlements:
                if settlement.name_he in existing_by_name:
                    connection.execute(
                        """
                        UPDATE settlements
                        SET name_en = COALESCE(?, name_en),
                            lat = COALESCE(?, lat),
                            lon = COALESCE(?, lon),
                            centroid_lat = COALESCE(?, centroid_lat),
                            centroid_lon = COALESCE(?, centroid_lon),
                            polygon = COALESCE(?, polygon),
                            geometry = COALESCE(?, geometry),
                            source_dataset = ?,
                            source_path = COALESCE(?, source_path)
                        WHERE id = ?
                        """,
                        (
                            settlement.name_en,
                            settlement.lat,
                            settlement.lon,
                            settlement.centroid_lat,
                            settlement.centroid_lon,
                            settlement.polygon,
                            settlement.geometry,
                            settlement.source_dataset,
                            settlement.source_path,
                            existing_by_name[settlement.name_he],
                        ),
                    )
                else:
                    cursor = connection.execute(
                        """
                        INSERT INTO settlements (name_he, name_en, lat, lon, centroid_lat, centroid_lon, polygon, geometry, source_dataset, source_path)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            settlement.name_he,
                            settlement.name_en,
                            settlement.lat,
                            settlement.lon,
                            settlement.centroid_lat,
                            settlement.centroid_lon,
                            settlement.polygon,
                            settlement.geometry,
                            settlement.source_dataset,
                            settlement.source_path,
                        ),
                    )
                    existing_by_name[settlement.name_he] = int(cursor.lastrowid)
            rows = connection.execute("SELECT id, name_he FROM settlements").fetchall()
            connection.commit()
        return {name_he: settlement_id for settlement_id, name_he in rows}

    def bulk_upsert_aliases(self, aliases: list[SettlementAliasSeed]) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.executemany(
                """
                INSERT INTO settlement_aliases (settlement_id, alias, alias_type, confidence, notes)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(alias) DO UPDATE SET
                    settlement_id = excluded.settlement_id,
                    alias_type = excluded.alias_type,
                    confidence = excluded.confidence,
                    notes = excluded.notes
                """,
                [
                    (
                        alias.settlement_id,
                        alias.alias,
                        alias.alias_type,
                        alias.confidence,
                        alias.notes,
                    )
                    for alias in aliases
                ],
            )
            connection.commit()
