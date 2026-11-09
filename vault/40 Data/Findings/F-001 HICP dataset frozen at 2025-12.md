---
type: finding
id: F-001
severity: high
status: resolved
area: data
found: 2026-11-08
resolved: 2026-11-09
tags:
  - finding
---

# F-001 · HICP dataset frozen at 2025-12

> [!finding] High severity · resolved 2026-11-09
> Every verified `prc_hicp_manr` series (BE, DE, FR, NL, EA20) ends at **2025-12** although the dataset was updated on 2026-02-06. Eurostat moved HICP to ECOICOP ver. 2 datasets.

## Impact
No current inflation series for the euro-area countries → none could reach `full` support.

## Resolution
Successor verified live: **`prc_hicp_minr`** with `freq=M, unit=RCH_A, coicop18=TOTAL` (all-items HICP, annual rate of change, ECOICOP ver. 2). Coverage **1997-01 → 2026-10** for BE, DE, FR, NL (358 months each); on the overlap with the old series the values differ by at most 0.1 pp. Ingested by `data-sync` on 2026-11-09. The 2026-10 value carries Eurostat's `e` (estimated) flag, stored as published.

## Action
Done: the catalog mapping is `prc_hicp_minr` (status verified). For Phase 8 point-in-time replay, `prc_hicp_fpd` (first-published releases) is a candidate vintage source, not yet probed.

Related: [[Eurostat]] · [[Phase 03 — Economic data ingestion & metadata]]
