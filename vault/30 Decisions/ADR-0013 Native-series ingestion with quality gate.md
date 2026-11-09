---
type: decision
id: ADR-0013
date: 2026-11-09
status: accepted
area: data
tags:
  - decision
---

# ADR-0013 · Native-series ingestion with quality gate

> [!decision] Decision
> Store each **native official series exactly as published** (levels, rates, event-dated decisions) and derive indicators (q/q, y/y, 12-month CPI change) at read time. Ingest with one `ingestion_run` per source, commit each series separately, and refuse to store a series that fails a hard quality rule. Freshness is measured from the **end** of the latest period.

## Context
- Several indicators share one series (GDP levels → q/q and y/y), and several countries share one (the ECB deposit rate for BE/DE/FR/NL). Storing derived values would duplicate data and hide the transformation.
- Sources fail independently: one bad series must neither erase the others nor leave a run looking green.
- The first live sync showed that measuring age from the period *start* calls normal release lags stale (quarterly government debt appears about t+115 days).

## Consequences
- `observations` is keyed by `(series_id, period)`. Re-runs are idempotent upserts that move provenance (`source_url`, `retrieved_at`, `source_updated_at`, `ingestion_run_id`) to the newest run.
- Hard rules (`non_empty`, `unique_periods`) reject the series. Soft rules (`gaps`, `freshness`, `plausible_range`, source flags, connector warnings) are stored as `warn` for the UI. Run status is `succeeded` / `partial` / `failed`; source freshness = the last run that fetched data (succeeded or partial).
- Growth is computed only where both periods exist, so gaps propagate (e.g. [[F-006 US October 2025 observations missing]]).
- Age limits: 90 days after month end, 150 after quarter end, 14 for daily series. Event-dated series (ECB decisions) have no age limit.
- Per-observation publication dates and vintages are **not** offered by these endpoints and stay unknown. Historical replays remain *revised-data / release-lag approximations* until ALFRED or first-release datasets are added.
