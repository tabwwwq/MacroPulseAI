---
type: status
phase: 10
phase_name: Hardening & release
updated: 2026-11-11
tags:
  - project
---

# 📍 Project status

## Now
- ✅ **Phase 1 — Foundation & design shell** done (`25366de`, 2026-11-08). See [[Phase 01 — Foundation & design shell]].
- ✅ **Phase 2 — Production-grade UI system** done (2026-11-09). See [[Phase 02 — Production-grade UI system]].
- ✅ **Phase 3 — Economic data ingestion & metadata** done (`90e0e91`, 2026-11-09). See [[Phase 03 — Economic data ingestion & metadata]].
- ✅ **Phase 4 — Data coverage & real dashboards** done (`51fb279`, 2026-11-09). See [[Phase 04 — Data coverage & real dashboards]].
- ✅ **Phase 5 — Recession target, features & first model** done (`ed7a1ab`, 2026-11-09) — published models do **not** beat the base rate on 2015+ held-out years ([[F-008 No model beats the base rate on held-out years]]). See [[Phase 05 — Recession target, features & first model]].
- ✅ **Phase 6 — Explainable risk dashboard & ML lab** done (2026-11-10): live inference round trip, explanations, risk timeline, ML laboratory. See [[Phase 06 — Explainable risk dashboard & ML lab]].
- ✅ **Phase 7 — Forecasts & scenario lab** done (2026-11-10): rolling-origin forecasts with measured interval coverage, scenario lab with bounded shocks and plausibility checks. Intervals under-cover ([[F-011 Forecast intervals under-cover]]). See [[Phase 07 — Forecasts & scenario lab]].
- ✅ **Phase 8 — Crisis time machine** done (2026-11-10): walk-forward replays with inputs as known then, outcomes as published later, warned / missed / false alarms; revised-data / release-lag approximation, no vintages. Most recessions were missed ([[F-013 Replays show most recessions were missed]]). See [[Phase 08 — Crisis time machine]].
- ✅ **Phase 9 — Analyst-grade PDF reports** done (2026-11-11): PDF / CSV / JSON country reports from the API's own services; renderers written by the **local model** (Qwen3.8-27B on the RX 7800 XT) and reviewed ([[ADR-0021 Local model as a reviewed single-file worker]]). See [[Phase 09 — Analyst-grade PDF reports]].
- ⏭️ **Phase 10 — Hardening & release** is next. See [[Phase 10 — Hardening & release]].
- CI: run 43012635167 for `baf7a97` (Phase 9) passed all jobs — Web, API, Docker images (with reportlab + matplotlib). Earlier phases green as well. (Earlier: the Docker job failed on `ed7a1ab`, fixed in `b6987da` — [[F-010 Docker build broke when the ML package was added]].)

## Working (verified 2026-11-10)
- Data: 31 native series, 25,702 observations; BE/DE/FR/NL `full`, US `partial`.
- Models: run `20261110T142434Z` (retrained to store the feature covariance; same selection) — H=2 HistGradientBoosting, H=4 Logistic Regression; artifacts in `models/artifacts`.
- API: `/api/recession/predict` (round trip, explanation, track record, in-sample flag), `/api/recession/history`, `/api/models` + `/metrics` + `/curves`, `/api/forecasts`, `/api/scenarios/spec` + `POST /evaluate` (rate-limited), `/api/history/replay` + `/episodes` + `/presets`, `POST /api/reports/generate`, plus all data endpoints.
- Web: Overview (live 2Q/4Q estimates with caveats), Countries, Compare, Data observatory, Recession risk, ML laboratory, Forecast studio, Scenario lab, Crisis time machine, **Report builder**.
- Checks: 254 pytest (+1 PostgreSQL in CI, +16 live), 102 Vitest, ruff, mypy `--strict`, ESLint, tsc, `next build`, `pnpm smoke` 2883/2883.
- Local model: llama.cpp Vulkan b12259 + Qwen3.8-27B Q3_K_XL in `~/.local/llama.cpp` and `~/.lmstudio/models` (outside the repo); `docs/LOCAL_MODEL.md`.

## Blockers & risks
- [[F-008 No model beats the base rate on held-out years]] — shown next to every probability.
- [[F-009 Separate horizon models can contradict each other]] — flagged in the UI, not resolved.
- [[F-011 Forecast intervals under-cover]] — coverage shown and flagged, method unchanged.
- [[F-012 Recession model lowers risk when unemployment rises]] — visible in the scenario lab, not tuned away.
- [[F-013 Replays show most recessions were missed]] — 2Q warned 0 / 20, 4Q 6 / 22; listed per recession on `/history`.
- [[F-006 US October 2025 observations missing]] — handled by the one-month staleness rule.
- [[F-002 OECD CLI missing for Belgium and Netherlands]] — no OECD connector.
- No vintages / publication dates → replays stay *revised-data approximations*; `FRED_API_KEY` not configured → US `partial`.
- [[F-007 OneDrive locks the virtual environment]] — also stale dev-server reloads; restart servers after edits.
- Browser-level E2E tests not automated; Docker not installed locally (CI builds the images).

## Next
1. Phase 10: hardening and release — security/secret audit (bundle, history, logs), shared rate limiting notes for multi-instance deploys, browser E2E for the main flows, Docker/compose verification in CI, README screenshots, deploy guide, final model and data refresh; consider the open findings ([[F-009 Separate horizon models can contradict each other]], [[F-011 Forecast intervals under-cover]], [[F-012 Recession model lowers risk when unemployment rises]], [[F-013 Replays show most recessions were missed]]).
