from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os


@dataclass(slots=True)
class PollingConfig:
    interval_seconds: float = 2.0
    request_timeout_seconds: float = 5.0
    max_retries: int = 3
    archive_raw_payloads: bool = True
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


@dataclass(slots=True)
class AppSettings:
    project_root: Path
    data_dir: Path
    raw_data_dir: Path
    normalized_data_dir: Path
    docs_dir: Path
    database_path: Path
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
        database_path = Path(os.environ.get("ALARMS_STA_DB_PATH", data_dir / "alarms_sta.db")).resolve()
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
                interval_seconds=float(os.environ.get("ALARMS_STA_POLL_INTERVAL", "2")),
                request_timeout_seconds=float(os.environ.get("ALARMS_STA_REQUEST_TIMEOUT", "5")),
                max_retries=int(os.environ.get("ALARMS_STA_MAX_RETRIES", "3")),
                archive_raw_payloads=os.environ.get("ALARMS_STA_ARCHIVE_RAW", "1") in {"1", "true", "TRUE", "yes", "YES"},
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
            ),
        )

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.normalized_data_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
