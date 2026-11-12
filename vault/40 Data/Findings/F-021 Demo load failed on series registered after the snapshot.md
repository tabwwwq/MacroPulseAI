---
type: finding
id: F-021
severity: medium
status: resolved
area: tooling
found: 2026-11-12
tags:
  - finding
---

# F-021 · Demo load failed on series registered after the snapshot

> [!finding] Medium · resolved
> CI run 43264272331 for `061dcce`: *E2E* and *Docker compose stack* failed at the demo step. `macropulse demo-load` loaded all 25,702 snapshot rows, then tried the 13 new OECD series, found them "not in the demo snapshot", recorded a failed OECD ingestion run and exited 1. Reproduced locally on a fresh database.

## Why the local checks missed it
The local Playwright run used the developer database, which already held live OECD data; only CI starts from the demo snapshot. The demo path was not exercised after the registry grew.

## Action
- `load_snapshot` imports only series the snapshot contains (`run_sync(..., series_ids=...)`); series registered later are listed as *not in this snapshot (registered after it was captured)* and stay *never synced*, which is the truth. A missing series is not a failed sync.
- Test `test_series_registered_after_the_snapshot_are_not_failures` loads the bundled snapshot and expects 13 OECD series reported, no failed run.
- Verified on a fresh database: `db upgrade`, `demo-load` (exit 0), `train` (same published models), then Playwright against that database.
- Practice: before pushing a change that adds registry series, replay CI's demo step on a fresh database.

Related: [[ADR-0022 Demo from a genuine snapshot, labelled as such]], [[ADR-0027 OECD connector with confidence indicators kept apart from the CLI]]
