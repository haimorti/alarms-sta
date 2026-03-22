# Data Inventory — Initial Stage 1 Assessment

## High-value existing assets

| Path | What already exists | Planned role in new system |
| --- | --- | --- |
| `data/alarms.csv` | Historical alarm rows with time, city, threat, id, description, and origin | Historical alarms corpus for analysis, validation, and later transition-rate features |
| `data/coord.csv` | Point coordinates for many locations (`loc`, `lat`, `long`) | Primary coordinates seed for settlement registry |
| `data/location_dictionary.csv` | Hebrew/English naming dictionary | Search and normalization support |
| `data/coord_area.csv` | Partial polygon-like point sequences for selected locations/sub-areas | Seed for geometry-aware extensions where area data exists |
| `data/coord_area.tsv` | Additional polygon-like rows, but currently messy and not normalized | Candidate source for later cleanup/import |
| `data/missing_cities.json` | Alias and unresolved-name mapping hints | Alias normalization bootstrap |
| `data/time_to_impact.csv` | Alarm timing metadata per city | Optional future enrichment feature, not required for MVP |
| `data/war23_alarms_monthly.csv` | Historical aggregate analysis table | Research/dashboard validation input |
| `data/war23_alarms_by_month_and_distance.csv` | Historical distance-based aggregates | Research validation input for later spatial calibration |

## What the repository already gives us
The existing data is a strong **starting point**, but not a complete mapping package for robust relative-position scoring.

### Already available
- A large point-based settlement/location list.
- Some alias hints.
- Some partial area/polygon data.
- Historical alarm history for calibration.

### Still incomplete for the long term
- A fully curated settlement registry with stable IDs.
- Consistent polygons for all relevant settlements, neighborhoods, bases, roads, industrial areas, and special locations.
- A complete alias table with review workflow.
- A canonical map of non-municipal entities that appear in alerts.

## Practical use in Stage 1
- Keep the existing `data/` directory intact.
- Add `data/raw/` for new live payload archives.
- Add `data/normalized/` for derived research outputs and exports.
- Do not overwrite legacy CSV files.
- Treat historical CSVs as source material for later import jobs, not as the operational database.

## What we may still need from the user
For a truly robust geo layer, the most valuable missing inputs would be:
1. An authoritative settlement/alert-entity list if one already exists outside the repo.
2. Any curated polygon or boundary files for settlements, neighborhoods, facilities, roads, and special alert zones.
3. Any existing mapping between Oref alert labels and canonical internal place IDs.
4. Any manually verified alias spreadsheet beyond `missing_cities.json`.

## Immediate follow-up for Stage 2
1. Profile `data/alarms.csv` in detail: duplicates, threat distribution, unique locations, time coverage.
2. Compare all unique alarm locations against `coord.csv` and alias hints.
3. Build a seed import pipeline into `settlements` and `settlement_aliases`.
4. Start collecting real raw JSON payloads from the live source into `data/raw/`.
