---
type: decision
id: ADR-0022
date: 2026-11-11
status: accepted
area: data
tags:
  - decision
---

# ADR-0022 · Demo from a genuine snapshot, labelled as such

> [!decision] Decision
> The credential-free demo loads `data/demo/snapshot-2026-11-09.json.gz`: the exact observations, flags, request URLs and retrieval times of the live sync of 2026-11-09 (31 series, 25,702 rows, 108 KB). It goes through the normal sync pipeline with a snapshot fetch function; ingestion runs are stored with `mode = "snapshot"` and the capture time, and the UI shows a DEMO banner while snapshot data is in use.

## Why
- CLAUDE.md §11 requires a one-command demo without credentials and with a prominent banner; §4 allows "an import from a genuine cached snapshot with source/date". No value is synthetic or edited.
- Reusing `run_sync` keeps validation and quality checks identical to a live sync and made the round trip testable (export → load reproduces every stored row exactly).
- Without the `mode`/`snapshot_taken_at` columns the data would look freshly synced at import time — a false freshness claim. Freshness is therefore the capture time.

## Consequences
- `pnpm demo` = bootstrap, `demo-load`, `train`, `dev`; CI uses the same snapshot to run the E2E suite and to load PostgreSQL in the compose job — realistic data without network.
- The snapshot ages like any download; `pnpm data:sync` replaces it and the banner disappears.
- Sources and terms per series: `data/demo/README.md`.

Related: [[Phase 10 — Hardening & release]] · [[ADR-0013 Native-series ingestion with quality gate]]
