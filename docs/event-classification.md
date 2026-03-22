# Event Classification

## Stage 2 / Stage 3 principle
Classification is intentionally cautious. The system must not assume that every payload from the alerts endpoint is an actual alarm.

## Current Stage 2 heuristics
The current parser/classifier is still preliminary and intended as scaffolding:
- extract candidate records from list payloads or common wrapper keys such as `data`, `alerts`, and `items`
- read possible metadata from `id`, `title`, `cat`, and `desc`
- extract location labels from common keys such as `cities`, `data`, `locations`, `areaNames`, and `settlements`
- classify using explicit keyword matches only

## Current keyword-driven categories
- `early_warning`: phrases such as `מוקדמת` / `early warning`
- `actual_alarm`: phrases such as `ירי רקטות`, `צבע אדום`, `חדירת כלי טיס עוין`, `חדירת מחבלים`
- `clear`: phrases such as `סיום`, `הסתיים`, `all clear`
- otherwise: `unknown`

## Important limitation
This is not yet a production classifier. It is a transparent starting point so that real payloads can be collected, reviewed, and converted into stronger classification rules with confidence tracking.

## Historical reference note
`data/alarms.csv` is useful as a historical reference because it preserves fields such as `time`, `cities`, `threat`, `id`, `description`, and `origin`, but it is already a simplified historical table. It should therefore inform research and validation, not replace raw-payload preservation or be treated as a complete representation of the live source schema.
