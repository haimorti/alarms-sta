from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from src.clustering.matcher import EventMatcher, MatchingPolicy, build_matching_policy
from src.clustering.service import ClusteringService
from src.api.service import ApiService
from src.db.clusters import EventClusterRepository
from src.config.settings import AppSettings
from src.db.bootstrap import initialize_database
from src.db.normalized_events import NormalizedEventRepository
from src.db.risk_windows import RiskWindowRepository
from src.db.raw_events import RawEventRepository
from src.db.settlements import SettlementRepository
from src.geo.registry import SeedImportResult, SettlementRegistryService
from src.geo.risk_windows import RiskWindowService
from src.scoring.engine import ProbabilityEngineV1
from src.ingestion.service import IngestionService
from src.ingestion.poller import PollerStatus, build_poller_status
from src.normalization.service import NormalizationService
from src.scoring.model import ScoringThresholds, build_scoring_thresholds

logger = logging.getLogger(__name__)
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@dataclass(slots=True)
class BootstrapArtifacts:
    settings: AppSettings
    poller_status: PollerStatus
    matching_policy: MatchingPolicy
    scoring_thresholds: ScoringThresholds
    ingestion_service: IngestionService
    normalization_service: NormalizationService
    settlement_registry: SettlementRegistryService
    seed_import_result: SeedImportResult
    clustering_service: ClusteringService
    probability_engine: ProbabilityEngineV1
    api_service: ApiService
    risk_window_service: RiskWindowService


def bootstrap_application(settings: AppSettings) -> BootstrapArtifacts:
    settings.ensure_directories()
    initialize_database(settings.database_path)
    raw_event_repository = RawEventRepository(settings.database_path)
    normalized_event_repository = NormalizedEventRepository(settings.database_path)
    settlement_repository = SettlementRepository(settings.database_path)
    event_cluster_repository = EventClusterRepository(settings.database_path)
    risk_window_repository = RiskWindowRepository(settings.database_path)

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
    settlement_registry = SettlementRegistryService(
        project_root=REPOSITORY_ROOT,
        repository=settlement_repository,
    )
    seed_import_result = settlement_registry.import_seed_data()
    ingestion_service = IngestionService(settings)
    normalization_service = NormalizationService(
        raw_event_repository=raw_event_repository,
        normalized_event_repository=normalized_event_repository,
        settlement_registry=settlement_registry,
    )
    clustering_service = ClusteringService(
        repository=event_cluster_repository,
        matcher=EventMatcher(matching_policy),
    )
    probability_engine = ProbabilityEngineV1(
        database_path=settings.database_path,
        scoring_config=settings.scoring,
    )
    api_service = ApiService(
        database_path=settings.database_path,
        probability_engine=probability_engine,
    )
    risk_window_service = RiskWindowService(risk_window_repository)

    logger.info("Application bootstrap completed. Database initialized at %s", settings.database_path)
    return BootstrapArtifacts(
        settings=settings,
        poller_status=poller_status,
        matching_policy=matching_policy,
        scoring_thresholds=scoring_thresholds,
        ingestion_service=ingestion_service,
        normalization_service=normalization_service,
        settlement_registry=settlement_registry,
        seed_import_result=seed_import_result,
        clustering_service=clustering_service,
        probability_engine=probability_engine,
        api_service=api_service,
        risk_window_service=risk_window_service,
    )
