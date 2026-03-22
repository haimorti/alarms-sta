# Data Inventory — Initial Stage 1 Assessment

## High-value existing assets

| Path | Planned role in new system |
| --- | --- |
| `data/alarms.csv` | Historical alarms corpus for analysis, validation, and later transition-rate features |
| `data/coord.csv` | Primary coordinates seed for settlement registry |
| `data/location_dictionary.csv` | Hebrew/English dictionary for search and normalization support |
| `data/coord_area.csv` | Seed for geometry-aware extensions where area data exists |
| `data/missing_cities.json` | Alias and unresolved-name normalization hints |
| `data/time_to_impact.csv` | Optional future enrichment feature, not required for MVP |
| `data/war23_alarms_monthly.csv` | Historical aggregate analysis input, useful for research dashboards |
| `data/war23_alarms_by_month_and_distance.csv` | Historical aggregate validation input for later research |

## Practical use in Stage 1
- Keep the existing `data/` directory intact.
- Add `data/raw/` for new live payload archives.
- Add `data/normalized/` for derived research outputs and exports.
- Do not overwrite legacy CSV files.
- Treat historical CSVs as source material for later import jobs, not as the operational database.

## Immediate follow-up for Stage 2
1. Profile `data/alarms.csv` in detail: duplicates, threat distribution, unique locations, time coverage.
2. Compare all unique alarm locations against `coord.csv` and alias hints.
3. Build a seed import pipeline into `settlements` and `settlement_aliases`.
4. Start collecting real raw JSON payloads from the live source into `data/raw/`.
