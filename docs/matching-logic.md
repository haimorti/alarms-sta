# Matching Logic

## Goal
Link an `early_warning` event to the most plausible `actual_alarm` event without assuming an official shared event identifier exists.

## Current Stage 5 baseline
The current baseline matcher scores candidates using:
1. **Time proximity** — actual alarm must occur within the configured candidate window.
2. **Geographic overlap** — the actual alarm locations must overlap sufficiently with the early-warning locations.
3. **Subset relation** — if the actual alarm is a tighter subset of the early-warning area, the score increases.
4. **Event type compatibility** — only `actual_alarm` candidates are considered valid matches.

## Current scoring components
- `overlap_ratio`: overlap divided by the actual-alarm location count
- `subset_ratio`: overlap divided by the early-warning location count
- `time_score`: higher when the gap is shorter
- `subset_bonus`: extra weight when the subset ratio crosses the strong-subset threshold

## Current output
Each match attempt yields:
- `method`
- `score`
- `explanation`

## Current limitation
This is still a deterministic baseline matcher. It is intentionally simple and transparent so that later stages can calibrate thresholds and weights against real historical data.
