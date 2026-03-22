# Architecture Plan — Stage 1

## Objective
Stage 1 establishes a clean, modular foundation for a new probability-assessment system without yet claiming reliable live-event classification or prediction. The focus is on project structure, configuration, database bootstrap, documentation, and testable scaffolding.

## Layer separation
- **Data ingestion**: polling, retries, raw payload persistence, transport telemetry.
- **Normalization**: payload parsing, event-type classification, settlement-name extraction, confidence recording.
- **Geospatial**: settlement registry, aliases, coordinates, neighborhood and geometry support.
- **Clustering**: matching early warnings, actual alarms, and clearing messages into event clusters.
- **Scoring**: separate spatial scoring, historical scoring, weighted scoring, component-level explanations, and confidence tracking.
- **Persistence**: SQLite-first schema for local development, designed so it can later migrate to PostgreSQL if needed.
- **API**: internal read/debug endpoints.
- **UI**: thin presentation layer only.

## Stage 1 deliverables
1. New `src/` module tree aligned with the requested architecture.
2. Config-driven bootstrap via environment variables.
3. Initial SQLite schema covering raw events, normalized events, settlement registry, cluster linkage, and probability snapshots.
4. Minimal application bootstrap that creates directories and initializes the database.
5. Documentation for data inventory and MVP scope.
6. Unit and integration tests for configuration and bootstrap.

## Stage 2 to Stage 5 baseline scaffolding now in place
- **Ingestion scaffolding**: HTTP fetcher, raw payload archiver, duplicate-preserving raw event repository, and ingestion service orchestration.
- **Normalization scaffolding**: payload parser, keyword-based cautious classifier, persistence into `normalized_events` and `event_locations`, and parse-status updates on raw events.
- **Settlement registry baseline**: seed import from `coord.csv`, `location_dictionary.csv`, `coord_area.csv`, and `missing_cities.json`, plus canonical-name/alias resolution and unresolved reporting.
- **Clustering baseline**: deterministic early-warning to actual-alarm matcher using time proximity, overlap ratio, subset ratio, and event-type compatibility.
- **Fixtures**: example raw payloads under `tests/fixtures/raw/` for deterministic parser, classifier, and ingestion tests.

## Score model contract from day one
The product must never collapse all reasoning into one opaque output. The Stage 1 data contract therefore reserves separate fields for:
- **Spatial score**: relative position inside the early-warning area.
- **Historical score**: transition evidence from similar historical events or similar relative positions.
- **Weighted score**: configurable blend of spatial and historical components.
- **Confidence**: at minimum for the weighted output, and preferably per component as data quality improves.
- **Explanations**: short text for spatial, historical, and weighted outputs independently.

This prevents a future refactor where one monolithic score would need to be split apart after the fact.

## Out of scope for Stage 1
- Live polling loop.
- Production-grade API server.
- UI rendering.
- Real event classification logic.
- Real geospatial scoring.

## Why the existing `data/` directory matters
The repository already includes historical alarms, coordinates, naming dictionaries, and alias hints. Stage 1 therefore treats `data/` as a first-class asset for:
- historical analysis,
- settlement seed loading,
- alias normalization,
- deterministic test fixtures,
- later calibration work.
