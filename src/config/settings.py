from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os

from src.db.sqlite import SHARED_MEMORY_DB_URI


@dataclass(slots=True)
class PollingConfig:
    interval_seconds: float = 3.0
    request_timeout_seconds: float = 5.0
    max_retries: int = 3
    archive_raw_payloads: bool = False
    user_agent: str = "alarms-sta/0.1"


@dataclass(slots=True)
class MatchingConfig:
    max_candidate_window_seconds: int = 180
    minimum_overlap_ratio: float = 0.5
    strong_subset_ratio: float = 0.8


@dataclass(slots=True)
class ScoringConfig:
    low_threshold: int = 33
    high_threshold: int = 66
    spatial_weight: float = 0.6
    historical_weight: float = 0.4


@dataclass(slots=True)
class AppSettings:
    project_root: Path
    data_dir: Path
    raw_data_dir: Path
    normalized_data_dir: Path
    docs_dir: Path
    database_path: str | Path
    log_level: str = "INFO"
    debug_mode: bool = False
    alerts_url: str = "https://www.oref.org.il/WarningMessages/Alert/alerts.json"
    polling: PollingConfig = field(default_factory=PollingConfig)
    matching: MatchingConfig = field(default_factory=MatchingConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)

    @classmethod
    def from_env(cls, project_root: Path | None = None) -> "AppSettings":
        root = Path(project_root or os.environ.get("ALARMS_STA_PROJECT_ROOT", Path.cwd())).resolve()
        data_dir = root / "data"
        raw_data_dir = Path(os.environ.get("ALARMS_STA_RAW_DIR", data_dir / "raw")).resolve()
        normalized_data_dir = Path(os.environ.get("ALARMS_STA_NORMALIZED_DIR", data_dir / "normalized")).resolve()
        docs_dir = root / "docs"
        database_path_env = os.environ.get("ALARMS_STA_DB_PATH")
        database_path = Path(database_path_env).resolve() if database_path_env else SHARED_MEMORY_DB_URI
        log_level = os.environ.get("ALARMS_STA_LOG_LEVEL", "INFO").upper()
        debug_mode = os.environ.get("ALARMS_STA_DEBUG", "0") in {"1", "true", "TRUE", "yes", "YES"}
        alerts_url = os.environ.get(
            "ALARMS_STA_ALERTS_URL",
            "https://www.oref.org.il/WarningMessages/Alert/alerts.json",
        )

        return cls(
            project_root=root,
            data_dir=data_dir,
            raw_data_dir=raw_data_dir,
            normalized_data_dir=normalized_data_dir,
            docs_dir=docs_dir,
            database_path=database_path,
            log_level=log_level,
            debug_mode=debug_mode,
            alerts_url=alerts_url,
            polling=PollingConfig(
                interval_seconds=float(os.environ.get("ALARMS_STA_POLL_INTERVAL", "3")),
                request_timeout_seconds=float(os.environ.get("ALARMS_STA_REQUEST_TIMEOUT", "5")),
                max_retries=int(os.environ.get("ALARMS_STA_MAX_RETRIES", "3")),
                archive_raw_payloads=os.environ.get("ALARMS_STA_ARCHIVE_RAW", "0") in {"1", "true", "TRUE", "yes", "YES"},
                user_agent=os.environ.get("ALARMS_STA_USER_AGENT", "alarms-sta/0.1"),
            ),
            matching=MatchingConfig(
                max_candidate_window_seconds=int(os.environ.get("ALARMS_STA_MATCH_WINDOW", "180")),
                minimum_overlap_ratio=float(os.environ.get("ALARMS_STA_MIN_OVERLAP", "0.5")),
                strong_subset_ratio=float(os.environ.get("ALARMS_STA_STRONG_SUBSET", "0.8")),
            ),
            scoring=ScoringConfig(
                low_threshold=int(os.environ.get("ALARMS_STA_LOW_THRESHOLD", "33")),
                high_threshold=int(os.environ.get("ALARMS_STA_HIGH_THRESHOLD", "66")),
                spatial_weight=float(os.environ.get("ALARMS_STA_SPATIAL_WEIGHT", "0.6")),
                historical_weight=float(os.environ.get("ALARMS_STA_HISTORICAL_WEIGHT", "0.4")),
            ),
        )
