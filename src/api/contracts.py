from __future__ import annotations

HEALTH_ENDPOINT = "/health"
ACTIVE_EVENTS_ENDPOINT = "/events/active"
SETTLEMENT_SEARCH_ENDPOINT = "/settlements/search"
CURRENT_PROBABILITY_ENDPOINT = "/probability/current"

PROBABILITY_COMPONENT_FIELDS = (
    "spatial_score",
    "spatial_label",
    "spatial_confidence",
    "spatial_confidence_label",
    "spatial_explanation",
    "historical_score",
    "historical_label",
    "historical_confidence",
    "historical_confidence_label",
    "historical_explanation",
    "weighted_score",
    "weighted_label",
    "weighted_confidence",
    "weighted_confidence_label",
    "weighted_explanation",
    "weighting_profile",
)
