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
- Preserve duplicate raw observations while still marking them as duplicates.
- Produce **three visible outputs** for the user:
  - spatial probability,
  - historical probability,
  - weighted total probability.
- Keep those outputs separate in the data model, API, and UI contract from day one.
- Expose explanations for each component and for the weighted result.
- Keep confidence separate from score, at least for the weighted result and ideally per component.
- Expose internal API endpoints for health, active events, and settlement probability lookup.

## What the MVP must not do
- Claim certainty.
- Present over-precise percentages without sufficient evidence.
- Collapse probability and confidence into one value.
- Collapse spatial and historical reasoning into one opaque score.
- Discard raw data.
- Depend solely on centroid distance.

## Output tone
Use cautious language such as:
- "Spatial probability inside the warning area: High"
- "Historical probability from similar events: Medium"
- "Weighted overall probability: High"
- "Confidence in weighted estimate: Medium"
