# Scoring Model

## Goal
Produce a cautious, explainable probability estimate that does not collapse reasoning into a single opaque number.

## Probability components
The current v1 engine emits three separate components:
- `spatial_*`
- `historical_*`
- `weighted_*`

Each component carries:
- numeric score
- label (`low` / `medium` / `high`)
- separate confidence
- explanation text

## Current v1 spatial features
- centroid centrality
- edge-distance proxy
- neighborhood density proxy

## Current v1 historical features
- historical early-warning count for the settlement
- matched transition count into actual alarms
- sample-quality-driven confidence

## Current v1 weighted output
The weighted output uses configurable weights:
- `spatial_weight`
- `historical_weight`

The weighted confidence is derived separately and also considers cluster match confidence.

## Important limitation
This is intentionally conservative. When historical data is missing or coordinate coverage is weak, the engine falls back to neutral scores with low confidence rather than pretending to know more than it does.
