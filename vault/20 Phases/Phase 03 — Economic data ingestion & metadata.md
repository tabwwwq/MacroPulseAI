---
type: phase
phase: 3
title: Economic data ingestion & metadata
status: done
started: 2026-11-09
completed: 2026-11-09
tags:
  - phase
---

# Phase 3 — Economic data ingestion & metadata

## Goal
Retrieve and store genuine official observations with provenance, quality checks and a `data-sync` CLI.

## Acceptance (abridged — full list in `docs/ROADMAP.md`)
- [x] Live-verified Eurostat GDP plus three more Eurostat datasets; ECB and FRED adapters live too
- [x] Observations store unit, frequency, seasonal adjustment, period, source URL/key, retrieval time and the source's dataset-update stamp; per-observation publication dates are not offered by these endpoints and stay unknown (no vintages yet)
- [x] Retries with backoff, `Retry-After`, per-host throttling, idempotent upserts, per-series commits, partial-failure handling
- [x] Source-health API backed by real ingestion runs; real row counts reported

## What was built
- `macropulse_economics.connectors`: Eurostat JSON-stat, ECB SDMX CSV, FRED graph CSV, one `Fetcher` with timeouts, retries and throttling.
- `series.py` turns the indicator catalog into **24 native series** (GDP levels feed both q/q and y/y; the ECB rate is fetched once for all euro-area members).
- `transforms.py`: growth only where both periods were published (no interpolation). `quality.py`: non-empty, unique periods, gaps, freshness, plausible range, source flags.
- `observations` + `quality_checks` tables (migration `0002`), `services/sync.py`, CLI `uv run macropulse data-sync [--source] [--country]`.
- `GET /api/indicators?country=&indicator=&start=&end=`: derived series + provenance + latest quality checks. Catalog, country support and source health now count real rows.
- Decision: [[ADR-0013 Native-series ingestion with quality gate]].

## Live result (2026-11-09)
| Source | Native series | Rows stored | Runs |
| --- | --- | --- | --- |
| Eurostat | 16 (GDP, HICP, unemployment, debt × BE/DE/FR/NL) | 4,417 | succeeded (2, 5) |
| ECB | 1 (deposit facility rate, euro area) | 69 | succeeded (1, 4) |
| FRED | 7 (GDPC1, CPIAUCSL, UNRATE, FEDFUNDS, GFDEGDQ188S, T10Y3M, USREC) | 16,608 | succeeded (3, 6) |

**21,094 observations** in about 13 s. The second run upserted the same 21,094 rows (idempotent). Support levels computed from stored data: **BE, DE, FR, NL `full`; US `partial`** (FRED metadata is not machine-verified without an API key).

## Log
- 2026-11-09 — HICP successor `prc_hicp_minr` verified (1997-01 → 2026-10) → [[F-001 HICP dataset frozen at 2025-12]] resolved.
- 2026-11-09 — Connectors, sync service, series endpoint; 121 pytest + 12 opt-in live tests (`MACROPULSE_LIVE_TESTS=1`) green.
- 2026-11-09 — First live sync exposed two issues: freshness measured from the period *start* flagged normal release lags → now measured from the period *end*; US October 2025 values are absent at the source → [[F-006 US October 2025 observations missing]].
- 2026-11-09 — `uv sync` failed on OneDrive placeholder folders inside `.venv` → [[F-007 OneDrive locks the virtual environment]].
- 2026-11-09 — UI copy that still said "connectors arrive in Phase 3" now follows the recorded runs and stored counts.
