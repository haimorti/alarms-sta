# MVP Scope

## MVP goal
Provide a cautious, explainable estimate for a selected settlement after it appears in an active early-warning area.

## What the MVP must do
- Poll the live alerts source.
- Persist every raw payload with timestamps and dedup hashes.
- Normalize events into a unified internal structure.
- Distinguish at least `early_warning` and `actual_alarm` with explicit classification confidence.
- Resolve settlement names through a registry and alias layer.
- Match related events into clusters using simple, explainable rules.
- Produce a provisional probability label and a separate confidence label.
- Expose internal API endpoints for health, active events, and settlement probability lookup.

## What the MVP must not do
- Claim certainty.
- Present over-precise percentages without sufficient evidence.
- Collapse probability and confidence into one value.
- Discard raw data.
- Depend solely on centroid distance.

## Output tone
Use cautious language such as:
- "Current probability assessment: High"
- "Confidence in estimate: Medium"
- "Assessment is based on relative position within the warning area and similar historical transitions"
