---
type: decision
id: ADR-0025
date: 2026-11-12
status: accepted
area: ml
tags:
  - decision
---

# ADR-0025 · Vintage replay re-fits the stored fold model and must reproduce it first

> [!decision] Decision
> For a US as-of quarter, the walk-forward fold model of that year is fitted again from the same panel, training rows, specification and seed. It is used only if it reproduces the stored walk-forward estimate on today's inputs (tolerance 1e-9). Then it scores a second input set: real GDP, CPI inflation and unemployment **as published on the cut-off date** (ALFRED vintage), market rates unchanged, same publication lags. Endpoint `GET /api/history/vintage-replay`; card *With the figures as first published* on `/history` (US only).

## Why
- The backtest stores predictions, not per-year fold models. Storing 27 folds × 2 horizons per run would be needless artefacts; re-fitting is cheap (well under a second per fold, cached per model version and year) and deterministic.
- The reproduction check makes drift visible instead of silent: if stored observations changed after training, the card says *Retrain* rather than comparing two different models.
- Training now records `panel_first_as_of` / `panel_last_as_of` in the evaluation protocol, so a re-fit never depends on the clock (older runs fall back to the creation date).
- Growth inputs come from levels of one vintage only (rule of [[ADR-0024 ALFRED vintages in separate tables with a first-release window]]); the transforms are the registry's, not hard-coded.

## What it does not change
The fold model was still trained on today's revised history and labels, and outcomes are judged on today's GDP. It answers "what would this model have said with the figures on the table then", not "what did anyone forecast". The main replay stays labelled *revised-data / release-lag approximation*.

## Consequences
- Tests: 6 API (rebased levels give the same estimate, first-release inputs used, market rates untouched, nothing after the cut-off, archive start, a drifted estimate is refused), 6 ML re-fit (exact reproduction for five model types), 3 E2E incl. axe.
- The local model wrote `vintage_series` and the card ([[ADR-0021 Local model as a reviewed single-file worker]]).

Related: [[F-018 First-release figures hid the 2008 downturn and amplified the 2022 false alarm]]
