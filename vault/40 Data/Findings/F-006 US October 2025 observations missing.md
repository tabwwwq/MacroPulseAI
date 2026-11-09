---
type: finding
id: F-006
severity: medium
status: open
area: data
found: 2026-11-09
tags:
  - finding
---

# F-006 · US October 2025 observations missing

> [!finding] Medium severity · open (source-side, likely permanent)
> The live sync of 2026-11-09 found FRED's missing-value marker `.` for **2025-10** in `CPIAUCSL` and `UNRATE` (quality checks `gaps` and `source_warning`, ingestion run 6). Stored periods go 2025-09 → 2025-11. This is consistent with the BLS not collecting October 2025 data during the Oct–Nov 2025 US federal government shutdown (context; the API response itself does not state a reason).

## Impact
- US CPI y/y is undefined for **2025-10**, and for **2026-10** once published (its base month is missing). The API returns no point rather than an interpolated one.
- Phase 5 features built from 12-month changes or monthly → quarterly averages for 2025-Q4 must handle a two-of-three-month quarter explicitly (missingness flag), not average two months as if complete.

## Action
Keep the gap. In Phase 5, define the quarterly aggregation rule (minimum months per quarter) and test it against this real gap.

Related: [[FRED]] · [[Phase 05 — Recession target, features & first model]]
