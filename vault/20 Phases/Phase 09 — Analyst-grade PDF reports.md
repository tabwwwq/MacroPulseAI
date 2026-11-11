---
type: phase
phase: 9
title: Analyst-grade PDF reports
status: done
started: 2026-11-10
completed: 2026-11-11
tags:
  - phase
---

# Phase 9 — Analyst-grade PDF reports

## Goal
Dated, source-cited reports with methodology and uncertainty notes.

## Acceptance (abridged — full list with evidence in `docs/ROADMAP.md`)
- [x] PDF opens and matches selected country/as-of — real DE and US 2008-Q2 reports reviewed page by page
- [x] Citations, units, dates, model versions, limitations
- [x] Rules-based executive summary (no invented analysis) — templates filled from recorded numbers; in-sample estimates said to be fits
- [x] CSV export of chart data — one row per point with citation and dates

## Delivered
- `reports/content.py` (contract), `services/report_builder.py`, `POST /api/reports/generate` (PDF / CSV / JSON, rate-limited, safe 500) ([[ADR-0020 Report renderers only lay out content]]).
- Renderers `reports/charts.py`, `reports/pdf.py`, `reports/csv_export.py` and the `/reports` page, **written by the local model** (Qwen3.8-27B on the RX 7800 XT) and reviewed ([[ADR-0021 Local model as a reviewed single-file worker]]).
- `scripts/agents/local_task.py`, `codex-task.ps1 -Local`, `docs/LOCAL_MODEL.md`.

## Verified
254 pytest · 102 Vitest · ruff/mypy `--strict`/ESLint/tsc · `next build` · `pnpm smoke` 2883/2883 · browser: PDF download (POST 200, descriptive filename), 375 px.

## Log
- 2026-11-10 — LM Studio not installed; ran the downloaded model with llama.cpp Vulkan b12259 instead (both files SHA-256 verified).
- 2026-11-10 — q8_0 KV cache + flash attention fell back to the CPU on Vulkan (prompt 6.7 tok/s); f16 cache: ~410 tok/s prompt, ~30 tok/s generation.
- 2026-11-10 — Codex `-Local` agentic run on the charts task: 31 min of reading, nothing written → [[F-014 Agentic Codex on the local model was unproductive]].
- 2026-11-11 — Switched to single-file delegation (`local_task.py`). Charts 2 rounds, CSV 1, PDF 3, page 1; every review issue recorded in `docs/LOCAL_MODEL.md`.
- 2026-11-11 — Own bugs found in review: in-sample estimates presented as forecasts in the summary (fixed + test), long native units, band note without bands, microseconds in timestamps, SDMX flag "A" shown as a flag.
