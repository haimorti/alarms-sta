from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PollerStatus:
    configured_url: str
    interval_seconds: float
    enabled: bool = False


def build_poller_status(configured_url: str, interval_seconds: float) -> PollerStatus:
    return PollerStatus(
        configured_url=configured_url,
        interval_seconds=interval_seconds,
        enabled=False,
    )
