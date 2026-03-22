from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SettlementProbabilityView:
    settlement_name: str
    in_active_early_warning: bool
    has_actual_alarm: bool
    probability_label: str
    confidence_label: str
    reason_summary: str
