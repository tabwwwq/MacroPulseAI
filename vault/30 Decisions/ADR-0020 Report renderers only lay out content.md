---
type: decision
id: ADR-0020
date: 2026-11-11
status: accepted
area: api
tags:
  - decision
---

# ADR-0020 · Report renderers only lay out content

> [!decision] Decision
> A report is a `ReportContent` value (`apps/api/src/macropulse_api/reports/content.py`) assembled by `services/report_builder.py` from the services the API already serves: KPI summary, stored series, live inference and forecast backtests. The PDF, chart and CSV renderers receive that value and only lay it out; they never fetch, compute or phrase numbers themselves.

## Why
- One source of truth: the report cannot disagree with the pages (tests and `pnpm smoke` compare the JSON report with `/api/countries/{iso}/summary`).
- The summary is template sentences filled with recorded numbers, so there is no free-form "analysis" to invent; a past as-of estimate is always stated as an in-sample fit next to its walk-forward value.
- A small, typed contract made the renderers safe to delegate to a weaker model ([[ADR-0021 Local model as a reviewed single-file worker]]).

## Details
- Libraries: reportlab (BSD) for the PDF, matplotlib (Agg backend, no pyplot) for charts, DejaVu Sans from matplotlib for full Unicode (−, ≥, ·).
- Formats: PDF, CSV of every chart point with citation and dates, JSON of the whole content. Filename `macropulse-report-<iso>-<as-of|latest>-<yyyymmdd>.<ext>`.
- No `report_exports` table: reports are generated on request, carry their own generation time, app version, as-of and sources, and are not stored.
- Failures in rendering become 500 `report_generation_failed` with a request id and no internals; the endpoint shares the compute rate limit.
- Key indicators keep the summary endpoint's as-of rule (periods ending by the cut-off, no publication lags), stated in the report's data basis and on the page.

Related: [[Phase 09 — Analyst-grade PDF reports]] · [[ADR-0016 Inference serving and explanations]] · [[ADR-0017 Forecasts from rolling-origin backtests]]
