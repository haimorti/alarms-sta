from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ScoreComponentView:
    score_label: str
    score_numeric: float | None
    confidence_label: str
    confidence_numeric: float | None
    explanation: str


@dataclass(slots=True)
class SettlementProbabilityView:
    settlement_name: str
    in_active_early_warning: bool
    has_actual_alarm: bool
    spatial_component: ScoreComponentView
    historical_component: ScoreComponentView
    weighted_component: ScoreComponentView
