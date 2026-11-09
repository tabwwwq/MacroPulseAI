---
type: finding
id: F-001
severity: high
status: open
area: data
found: 2026-11-08
tags:
  - finding
---

# F-001 · HICP dataset frozen at 2025-12

> [!finding] High severity · open
> Every verified `prc_hicp_manr` series (BE, DE, FR, NL, EA20) ends at **2025-12** although the dataset was updated on 2026-02-06. Eurostat appears to have moved HICP to new datasets.

## Impact
No current inflation series for the euro-area countries → none can reach `full` support yet.

## Action
Phase 3: discover and live-verify the successor dataset from Eurostat's catalogue; never fill the gap with the stale series.

Related: [[Eurostat]]
