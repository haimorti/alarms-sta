from __future__ import annotations

import logging
from dataclasses import dataclass

from src.clustering.matcher import MatchingPolicy, build_matching_policy
from src.config.settings import AppSettings
from src.db.bootstrap import initialize_database
from src.ingestion.service import IngestionService
from src.ingestion.poller import PollerStatus, build_poller_status
from src.normalization.service import NormalizationService
from src.scoring.model import ScoringThresholds, build_scoring_thresholds

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BootstrapArtifacts:
    settings: AppSettings
    poller_status: PollerStatus
    matching_policy: MatchingPolicy
    scoring_thresholds: ScoringThresholds
    ingestion_service: IngestionService
    normalization_service: NormalizationService


def bootstrap_application(settings: AppSettings) -> BootstrapArtifacts:
    settings.ensure_directories()
    initialize_database(settings.database_path)

    poller_status = build_poller_status(
        configured_url=settings.alerts_url,
        interval_seconds=settings.polling.interval_seconds,
    )
    matching_policy = build_matching_policy(
        max_candidate_window_seconds=settings.matching.max_candidate_window_seconds,
        minimum_overlap_ratio=settings.matching.minimum_overlap_ratio,
        strong_subset_ratio=settings.matching.strong_subset_ratio,
    )
    scoring_thresholds = build_scoring_thresholds(
        low_threshold=settings.scoring.low_threshold,
        high_threshold=settings.scoring.high_threshold,
    )
    ingestion_service = IngestionService(settings)
    normalization_service = NormalizationService(
        alias_file=settings.project_root / "data" / "missing_cities.json",
    )

    logger.info("Application bootstrap completed. Database initialized at %s", settings.database_path)
    return BootstrapArtifacts(
        settings=settings,
        poller_status=poller_status,
        matching_policy=matching_policy,
        scoring_thresholds=scoring_thresholds,
        ingestion_service=ingestion_service,
        normalization_service=normalization_service,
    )
