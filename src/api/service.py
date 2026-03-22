from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from src.db.probability_snapshots import ProbabilitySnapshotRepository
from src.geo.name_normalizer import compact_location_name, normalize_location_name
from src.scoring.engine import ProbabilityEngineV1, SettlementEventContext


class ApiService:
    def __init__(self, database_path: Path, probability_engine: ProbabilityEngineV1) -> None:
        self.database_path = database_path
        self.probability_engine = probability_engine
        self.snapshot_repository = ProbabilitySnapshotRepository(database_path)

    def health(self) -> dict[str, Any]:
        with sqlite3.connect(self.database_path) as connection:
            raw_count = connection.execute("SELECT COUNT(*) FROM raw_events").fetchone()[0]
            normalized_count = connection.execute("SELECT COUNT(*) FROM normalized_events").fetchone()[0]
            latest_fetch = connection.execute("SELECT MAX(fetched_at) FROM raw_events").fetchone()[0]
        return {
            "status": "ok",
            "raw_events": raw_count,
            "normalized_events": normalized_count,
            "last_fetch_at": latest_fetch,
        }

    def events_active(self, limit: int = 20) -> list[dict[str, Any]]:
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id, normalized_type, started_at, ended_at, source_event_id, confidence_in_classification
                FROM normalized_events
                ORDER BY started_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def events_history(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.events_active(limit=limit)

    def event_detail(self, event_id: int) -> dict[str, Any] | None:
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            event = connection.execute("SELECT * FROM normalized_events WHERE id = ?", (event_id,)).fetchone()
            if not event:
                return None
            locations = connection.execute(
                "SELECT * FROM event_locations WHERE normalized_event_id = ? ORDER BY location_name_raw",
                (event_id,),
            ).fetchall()
            risk_windows = connection.execute(
                "SELECT * FROM risk_windows WHERE normalized_event_id = ? ORDER BY phase_index DESC, id DESC",
                (event_id,),
            ).fetchall()
        payload = dict(event)
        payload["locations"] = [dict(row) for row in locations]
        payload["risk_windows"] = [dict(row) for row in risk_windows]
        return payload

    def settlements_search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        normalized = normalize_location_name(query)
        compact = compact_location_name(query)
        needle = f"%{query}%"
        normalized_needle = f"%{normalized}%"
        compact_needle = f"%{compact}%"
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT DISTINCT s.id, s.name_he, s.name_en, s.lat, s.lon
                FROM settlements s
                LEFT JOIN settlement_aliases sa ON sa.settlement_id = s.id
                WHERE s.name_he LIKE ?
                   OR COALESCE(s.name_he_normalized, '') LIKE ?
                   OR COALESCE(s.name_he_compact, '') LIKE ?
                   OR COALESCE(s.name_en, '') LIKE ?
                   OR COALESCE(sa.alias, '') LIKE ?
                   OR COALESCE(sa.alias_normalized, '') LIKE ?
                   OR COALESCE(sa.alias_compact, '') LIKE ?
                ORDER BY CASE
                    WHEN s.name_he = ? THEN 0
                    WHEN COALESCE(s.name_he_normalized, '') = ? THEN 1
                    WHEN COALESCE(s.name_he_compact, '') = ? THEN 2
                    ELSE 3
                END, s.name_he
                LIMIT ?
                """,
                (needle, normalized_needle, compact_needle, needle, needle, normalized_needle, compact_needle, query, normalized, compact, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def probability_current(self, settlement_query: str) -> dict[str, Any] | None:
        settlement = self._resolve_settlement(settlement_query)
        if not settlement:
            return None
        status = self._current_alert_status(settlement["id"])
        latest_alarm = self._latest_actual_alarm_for_settlement(settlement["id"])
        latest_event = self._latest_early_warning_for_settlement(settlement["id"])
        if not latest_event:
            return {
                "settlement": settlement,
                "message": "No active or historical early-warning event currently contains this settlement",
                "status": status,
                "latest_alarm": latest_alarm,
            }

        cluster_id = latest_event["id"]
        existing = self.snapshot_repository.latest_for_settlement_and_cluster(settlement["id"], cluster_id)
        latest_risk_window = self._latest_risk_window(cluster_id)
        if existing:
            return {
                "settlement": settlement,
                "event_id": latest_event["id"],
                "snapshot": existing,
                "risk_window": latest_risk_window,
                "status": status,
                "latest_alarm": latest_alarm,
            }

        context = SettlementEventContext(
            cluster_id=cluster_id,
            settlement_id=settlement["id"],
            settlement_name=settlement["name_he"],
            settlement_lat=settlement.get("lat"),
            settlement_lon=settlement.get("lon"),
            event_locations=self._event_locations(latest_event["id"]),
            cluster_match_confidence=0.5,
            trajectory_confidence=float(latest_risk_window["trajectory_confidence"]) if latest_risk_window else 0.5,
            risk_phase_label=str(latest_risk_window["phase_label"]) if latest_risk_window else "current_estimate",
        )
        snapshot_id = self.probability_engine.evaluate_and_persist(context)
        snapshot = self.snapshot_repository.latest_for_settlement_and_cluster(settlement["id"], cluster_id)
        return {
            "settlement": settlement,
            "event_id": latest_event["id"],
            "snapshot_id": snapshot_id,
            "snapshot": snapshot,
            "risk_window": latest_risk_window,
            "status": status,
            "latest_alarm": latest_alarm,
        }

    def probability_history(self, settlement_query: str, limit: int = 20) -> dict[str, Any] | None:
        settlement = self._resolve_settlement(settlement_query)
        if not settlement:
            return None
        history = self.snapshot_repository.history_for_settlement(settlement["id"], limit=limit)
        return {"settlement": settlement, "history": history}

    def debug_raw_events(self, limit: int = 20) -> list[dict[str, Any]]:
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT id, fetched_at, source_url, payload_hash, parse_status, is_duplicate, duplicate_of_raw_event_id FROM raw_events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def debug_normalized_events(self, limit: int = 20) -> list[dict[str, Any]]:
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT id, raw_event_id, normalized_type, started_at, source_event_id, confidence_in_classification FROM normalized_events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _resolve_settlement(self, query: str) -> dict[str, Any] | None:
        results = self.settlements_search(query, limit=1)
        return results[0] if results else None

    def _latest_early_warning_for_settlement(self, settlement_id: int) -> dict[str, Any] | None:
        return self._latest_event_for_settlement(settlement_id, 'early_warning')

    def _latest_actual_alarm_for_settlement(self, settlement_id: int) -> dict[str, Any] | None:
        return self._latest_event_for_settlement(settlement_id, 'actual_alarm')

    def _latest_clear_event(self, settlement_id: int) -> dict[str, Any] | None:
        return self._latest_event_for_settlement(settlement_id, 'clear')

    def _latest_event_for_settlement(self, settlement_id: int, event_type: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT ne.*
                FROM normalized_events ne
                JOIN event_locations el ON el.normalized_event_id = ne.id
                WHERE ne.normalized_type = ? AND el.settlement_id = ?
                ORDER BY ne.started_at DESC, ne.id DESC
                LIMIT 1
                """,
                (event_type, settlement_id),
            ).fetchone()
        return dict(row) if row else None

    def _current_alert_status(self, settlement_id: int) -> dict[str, Any]:
        candidates = [
            event
            for event in (
                self._latest_early_warning_for_settlement(settlement_id),
                self._latest_actual_alarm_for_settlement(settlement_id),
                self._latest_clear_event(settlement_id),
            )
            if event
        ]
        if not candidates:
            return {"state": "quiet", "title": "אין התרעה פעילה כרגע"}
        latest = max(candidates, key=lambda item: (item.get('started_at') or '', item.get('id') or 0))
        if latest['normalized_type'] == 'clear':
            return {"state": "ended", "title": "האירוע הסתיים", "event": latest}
        if latest['normalized_type'] == 'actual_alarm':
            return {"state": "alarm", "title": "צבע אדום", "event": latest}
        return {"state": "warning", "title": "צפויות להתקבל התרעות", "event": latest}

    def _event_locations(self, event_id: int) -> list[dict[str, Any]]:
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT location_name_raw, location_name_normalized, settlement_id, lat, lon FROM event_locations WHERE normalized_event_id = ?",
                (event_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _latest_risk_window(self, cluster_id: int) -> dict[str, Any] | None:
        with sqlite3.connect(self.database_path) as connection:
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
