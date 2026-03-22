# Data Model

## `raw_events`
Stores every fetched payload observation, including duplicates.

Key fields:
- `fetched_at`: exact fetch timestamp.
- `source_payload`: raw JSON payload as received.
- `source_url`: source endpoint.
- `payload_hash`: deterministic payload hash for dedup detection.
- `http_status`: transport status when available.
- `response_latency_ms`: transport latency.
- `archive_path`: file path under `data/raw/` when archived.
- `is_duplicate`: whether this payload hash was already seen before.
- `duplicate_of_raw_event_id`: first matching raw event if duplicate.
- `parse_status`: pending / parsed / failed.

## `normalized_events`
Stores the cautious normalized interpretation of raw events.

Key fields:
- `normalized_type`: `early_warning`, `actual_alarm`, `clear`, `unknown`, or `other`.
- `confidence_in_classification`: confidence in event type assignment.
- `notes`: machine-readable or human-readable classification notes.

## `event_locations`
Stores extracted raw location labels and their normalized settlement resolution. The resolved coordinates currently use the canonical settlement centroid so later scoring can measure distance-to-center, edge exposure, and other spatial heuristics.

## `settlements`
Canonical settlement / alert-entity registry.

Key fields:
- `centroid_lat` / `centroid_lon`: primary spatial point derived from municipal polygons when available.
- `polygon`: serialized GeoJSON polygon or multipolygon retained for later precise scoring.
- `source_dataset` / `source_path`: provenance for the geometry seed, with `data/israel-municipalities-polygons-master/` treated as the primary source.

## `settlement_aliases`
Alias mapping layer used to normalize alert labels to canonical entities.

## `event_clusters`
Cluster-level matching between early warning, actual alarm, and clear events.

## `cluster_members`
Links normalized events into a cluster with a role and membership score.

## `probability_snapshots`
Stores the product-facing probability breakdown.

Key fields:
- `spatial_*`: score, label, confidence, explanation for relative position in warning area.
- `historical_*`: score, label, confidence, explanation for historical transition evidence.
- `weighted_*`: score, label, confidence, explanation for the final weighted result.
- `weighting_profile`: serialized description of component weights used.


## `risk_windows`
Stores the time-evolving uncertainty windows for a cluster, such as initial wide launch-detection ellipses and later narrower refined-warning zones.

Key fields:
- `phase_index`: ordering of the trajectory/risk-estimate evolution.
- `phase_label`: semantic stage such as initial detection, refined warning zone, or final alert window.
- `geometry_kind` / `geometry_payload`: serialized representation of the uncertainty area.
- `trajectory_confidence`: confidence in the current trajectory estimate.
