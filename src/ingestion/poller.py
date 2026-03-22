from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import requests

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PollerStatus:
    configured_url: str
    interval_seconds: float
    enabled: bool = False


@dataclass(slots=True)
class FetchedPayload:
    fetched_at: datetime
    source_url: str
    payload_text: str
    payload_hash: str
    payload_json: Any
    http_status: int
    response_latency_ms: float


class AlertFetcher:
    def __init__(self, configured_url: str, timeout_seconds: float, user_agent: str) -> None:
        self.configured_url = configured_url
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent

    def fetch_once(
        self,
        request_get: Callable[..., requests.Response] | None = None,
    ) -> FetchedPayload:
        request_get = request_get or requests.get
        started = time.perf_counter()
        response = request_get(
            self.configured_url,
            timeout=self.timeout_seconds,
            headers={"User-Agent": self.user_agent},
        )
        latency_ms = (time.perf_counter() - started) * 1000
        response.raise_for_status()
        payload_text = response.text
        payload_json = response.json()
        payload_hash = hashlib.sha256(payload_text.encode("utf-8")).hexdigest()
        fetched_at = datetime.now(timezone.utc)
        logger.info(
            "Fetched alerts payload from %s with status=%s latency_ms=%.2f",
            self.configured_url,
            response.status_code,
            latency_ms,
        )
        return FetchedPayload(
            fetched_at=fetched_at,
            source_url=self.configured_url,
            payload_text=payload_text,
            payload_hash=payload_hash,
            payload_json=payload_json,
            http_status=response.status_code,
            response_latency_ms=latency_ms,
        )


class RawPayloadArchiver:
    def __init__(self, raw_data_dir: Path) -> None:
        self.raw_data_dir = raw_data_dir

    def archive(self, payload: FetchedPayload) -> Path | None:
        logger.warning("Raw payload archiving is disabled in runtime-safe mode; skipping disk write for %s", payload.source_url)
        return None


def build_poller_status(configured_url: str, interval_seconds: float) -> PollerStatus:
    return PollerStatus(
        configured_url=configured_url,
        interval_seconds=interval_seconds,
        enabled=False,
    )
