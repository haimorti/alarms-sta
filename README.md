# Alarms STA

## Project goal
This repository is being extended into a new, modular system for estimating the probability that a specific settlement will receive an actual alarm after appearing in an early-warning area. The system is intentionally conservative: it separates what is observed from what is inferred, preserves raw data, and explains every meaningful decision.

## Current status
Stage 1 is now focused on infrastructure:
- modular project skeleton under `src/`,
- config-driven bootstrap,
- initial SQLite schema,
- documentation for architecture and MVP scope,
- tests for configuration and bootstrap,
- initial ingestion and normalization scaffolding with fixtures.

A key product rule is now encoded directly into the foundation: the future scoring layer must expose **three separate outputs** instead of one opaque score:
- spatial probability,
- historical probability,
- weighted total probability,
with explanations and confidence kept separate from the scores themselves.

## Repository context
The repository already contains historical alarm and geography data under `data/`. These legacy datasets are not treated as the operational database, but they are important inputs for:
- historical analysis,
- settlement seed loading,
- alias normalization,
- deterministic fixtures,
- later scoring calibration.

See:
- `docs/architecture-plan.md`
- `docs/data-inventory.md`
- `docs/data-model.md`
- `docs/event-classification.md`
- `docs/mvp-scope.md`

## Run Stage 1 bootstrap
```bash
PYTHONPATH=. python -m src.app.main
```

The bootstrap will:
1. create `data/raw/` and `data/normalized/` if they do not exist,
2. initialize the SQLite database at `data/alarms_sta.db`,
3. print the active configuration summary.

## Run tests
```bash
PYTHONPATH=. python -m unittest discover -s tests
```

## Legacy materials
The historical maps, one-off scripts, and older analyses remain in the repository for reference and research, but the new system is being built as a clean architecture alongside them.
