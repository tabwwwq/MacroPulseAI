---
type: decision
id: ADR-0024
date: 2026-11-12
status: accepted
area: data
tags:
  - decision
---

# ADR-0024 · ALFRED vintages in separate tables with a first-release window

> [!decision] Decision
> US revision histories (real GDP, CPI, unemployment) are fetched from ALFRED with the server-side `FRED_API_KEY` and stored in `vintage_series` / `vintage_observations` (migration 0005), apart from `observations`. A stored value counts as a **first release** only if it was published within **120 days** of its period's end; everything else is shown but excluded from statistics and signals.

## Why
- `observations` keeps meaning "latest revision"; every dashboard, model and replay reads it. Vintages are opt-in and labelled ("Vintage data"), so nothing changes silently.
- ALFRED's archive for real GDP starts 1991-12-04, and its 1992-12-22 vintage back-filled history to 1947. "First appearance in the archive" is therefore not a first release — the live data showed 1947–1958 "signals" that were really 1992 values. US GDP advance estimates come ~30 days after the quarter, CPI and unemployment within ~2 weeks; 120 days separates them cleanly from back-fills.
- Growth from vintages uses both levels from the same vintage: base years change between vintages (1987 → 2017 dollars), so cross-vintage level ratios are meaningless.
- The key is redacted from stored URLs and from errors; a failed refresh never deletes a stored history.

## Consequences
- `macropulse vintages-sync` (≈6 s) and `GET /api/vintages/revisions`; card "first release vs today" on the US Growth, Prices and Labor tabs; 503 with the sync instruction when nothing is stored.
- Not yet: vintage-backed replays or training — replays stay *revised-data approximations*. Next candidate.
- Local model wrote the client, the analytics module and the web helpers ([[ADR-0021 Local model as a reviewed single-file worker]]).

Related: [[F-017 ALFRED shows a 2022 technical recession that was revised away]]
