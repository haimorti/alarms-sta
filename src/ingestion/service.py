from __future__ import annotations

import logging
from dataclasses import dataclass

from src.config.settings import AppSettings
from src.db.raw_events import RawEventInsert, RawEventRecord, RawEventRepository
from src.ingestion.poller import AlertFetcher, FetchedPayload
from src.normalization.parser import extract_primary_metadata

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IngestionResult:
    fetched_payload: FetchedPayload
    raw_event_record: RawEventRecord


class IngestionService:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.fetcher = AlertFetcher(
            configured_url=settings.alerts_url,
            timeout_seconds=settings.polling.request_timeout_seconds,
            user_agent=settings.polling.user_agent,
        )
        self.repository = RawEventRepository(settings.database_path)

    def collect_once(self) -> IngestionResult:
        fetched_payload = self.fetcher.fetch_once()
        archive_path = None
        if self.settings.polling.archive_raw_payloads:
            logger.warning("Raw payload archiving requested but disabled in runtime-safe mode; payload will stay in memory only")

        metadata = extract_primary_metadata(fetched_payload.payload_json)
        raw_event_record = self.repository.save(
            RawEventInsert(
                fetched_at=fetched_payload.fetched_at,
                source_payload=fetched_payload.payload_json,
                source_url=fetched_payload.source_url,
                payload_hash=fetched_payload.payload_hash,
                source_event_id=metadata.source_event_id,
                title=metadata.title,
                category=metadata.category,
                description=metadata.description,
                http_status=fetched_payload.http_status,
                response_latency_ms=fetched_payload.response_latency_ms,
                archive_path=str(archive_path) if archive_path else None,
            )
        )
        logger.info(
            "Stored raw payload id=%s duplicate=%s duplicate_of=%s",
            raw_event_record.id,
            raw_event_record.is_duplicate,
            raw_event_record.duplicate_of_raw_event_id,
        )
        return IngestionResult(fetched_payload=fetched_payload, raw_event_record=raw_event_record)
