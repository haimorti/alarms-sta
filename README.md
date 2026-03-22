# Alarms STA

## Product direction
Alarms STA is evolving from a data pipeline into a user-facing product for estimating whether a specific settlement is likely to receive an actual alarm after appearing in an early-warning area. The product is intentionally conservative: it separates what is observed from what is inferred, preserves raw data, and explains every meaningful decision.

The user-facing product rule is explicit across the codebase: every settlement result shows three separate outputs instead of one opaque score:
- spatial probability,
- historical probability,
- weighted total probability,
with explanations and confidence kept separate from the scores themselves.

## What is implemented in this stage
- modular project skeleton under `src/`,
- config-driven bootstrap,
- SQLite operational schema,
- ingestion and normalization scaffolding,
- settlement registry seeded from municipal GeoJSON + legacy coordinate datasets,
- Hebrew-aware alias and normalization matching for settlement lookup,
- HTML product shell for the main page and settlement-result page,
- Vercel deployment entrypoint and configuration.

## Hebrew settlement handling
The settlement layer is now designed to handle names that arrive from the Home Front Command feed exactly as Hebrew strings in `data`, including:
- Hebrew-only names,
- names with spaces and hyphens,
- sub-areas such as `נתניה - מזרח`,
- non-municipal entities such as farms and industrial zones,
- mismatch cases where the feed name is not identical to the geographic registry name.

The matching flow is:
1. store canonical settlements from GeoJSON, `coord.csv`, `coord_area.csv`, and `missing_cities.json`,
2. generate normalized and compact Hebrew variants for both canonical names and aliases,
3. resolve by exact name, normalized name, compact name, then alias,
4. mark whether the matched settlement has a direct polygon or whether fallback centroid/geometry coverage was used.

## UX states
The UI is RTL and light-themed.

Main page:
- refreshes every 3 seconds,
- shows a clear quiet state when there is no active event,
- shows that an alert event exists when activity is present,
- includes settlement search and recent selections.

Settlement result page:
- shows whether the settlement is currently part of the event,
- shows spatial score, historical score, and weighted score separately,
- shows short explanations per score,
- shows final confidence,
- shows current alert state using the Home Front Command wording:
  - `צפויות להתקבל התרעות`,
  - `צבע אדום`,
  - `האירוע הסתיים`.

## Deployment choice
This project is prepared for **Vercel**.

Why Vercel fits better here:
- the current product is a lightweight Python app with a small HTML shell and API endpoints,
- Vercel's Python deployment path is simpler for a mixed HTML + JSON MVP than Netlify for this repository structure,
- routing everything through a single Python entrypoint keeps the deployment assumptions explicit and minimal.

Deployment files added:
- `api/index.py`
- `vercel.json`
- `requirements.txt`

## Local run
Bootstrap:
```bash
PYTHONPATH=. python -m src.app.main
```

Tests:
```bash
PYTHONPATH=. python -m unittest discover -s tests
```
