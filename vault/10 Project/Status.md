---
type: status
phase: 10
phase_name: Hardening & release (complete)
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
- ✅ **Phase 10 — Hardening & release** done (`75c88b5`, 2026-11-11): credential-free demo from a genuine snapshot ([[ADR-0022 Demo from a genuine snapshot, labelled as such]]), security audit and secret scanner, 58 Playwright E2E incl. axe ([[F-015 Accessibility violations found by the first axe run]]), compose stack on PostgreSQL in CI, deploy guide, README with real screenshots. See [[Phase 10 — Hardening & release]].
- 🎨 **Visual refresh** after the release (2026-11-11): new design system — opaque gradient-bordered panels, ambient backdrop, shared chart theme, redesigned gauge, KPI sparklines from stored series, pulse trace ([[ADR-0023 Opaque panels, shared chart theme and decorative motion]], `docs/DESIGN.md`). Five files written by the local model and reviewed. No data, model or caveat changed. CI for it: run 43090806778 for `18e3f06` passed all five jobs (API, Web, Security audit, E2E 58 Playwright incl. axe, Docker compose stack).
- All ten roadmap phases are complete. CI: run 43023762417 for `0dde5a0` passed all five jobs — API, Web, Security audit (history/tree secret scan, pip-audit, pnpm audit), E2E (58 Playwright on the demo snapshot) and the Docker compose stack on PostgreSQL. The previous run 43022549543 (`31ba843`) failed only the security scan on this phase's own fake test credentials; reviewed and allowlisted in `0dde5a0`.

## Working (verified 2026-11-11)
- Data: 31 native series, 25,702 observations; BE/DE/FR/NL `full`, US `partial`. The same rows ship as the demo snapshot `data/demo/snapshot-2026-11-09.json.gz` (`pnpm demo`, DEMO banner).
- Models: H=2 HistGradientBoosting, H=4 Logistic Regression; artifacts in `models/artifacts` (ignored); a fresh clone trains them in ~13 s.
- API: all endpoints of CLAUDE.md §9 except admin sync/train (CLI only, by design); 64 KiB body limit, security headers, credential redaction in stored provenance.
- Web: all ten pages on the refreshed design; production CSP; axe WCAG A/AA clean at 1440 px and 375 px (58/58 after the refresh); shell-shared queries are hydration-safe ([[F-016 Hydration mismatch from queries shared with the shell]]).
- Checks: 287 pytest (+1 PostgreSQL in CI, +16 live), 134 Vitest, ruff, mypy `--strict`, ESLint, tsc, `next build`, 58 Playwright, `pnpm smoke` 2883/2883, secret scan, `pip-audit`, `pnpm audit`.
- Clean clone: fresh `git clone` of `75c88b5` → bootstrap 3 min 28 s, demo load 6.6 s, train 12.8 s; 283 pytest, 104 Vitest, lint, build, smoke 2883/2883 all passed.
- Local model: llama.cpp Vulkan b12259 + Qwen3.8-27B Q3_K_XL outside the repo; `docs/LOCAL_MODEL.md`.

## Blockers & risks
- [[F-008 No model beats the base rate on held-out years]] — shown next to every probability.
- [[F-009 Separate horizon models can contradict each other]] — flagged in the UI, not resolved.
- [[F-011 Forecast intervals under-cover]] — coverage shown and flagged, method unchanged.
- [[F-012 Recession model lowers risk when unemployment rises]] — visible in the scenario lab, not tuned away.
- [[F-013 Replays show most recessions were missed]] — 2Q warned 0 / 20, 4Q 6 / 22; listed per recession on `/history`.
- [[F-006 US October 2025 observations missing]] — handled by the one-month staleness rule.
- [[F-002 OECD CLI missing for Belgium and Netherlands]] — no OECD connector.
- No vintages / publication dates → replays stay *revised-data approximations*. `FRED_API_KEY` is configured in the local `.env` since 2026-11-11 (verified: FRED `series` and ALFRED `vintagedates` for GDPC1 answer 200; the API reports it as configured) — but no connector uses it yet, so US stays `partial` until the ALFRED client is built.
- [[F-007 OneDrive locks the virtual environment]] — also stale dev-server reloads; restart servers after edits.
- Docker not installed locally: the compose stack is verified in CI only.

## Next
Release work is finished; remaining items are improvements, not gaps in the delivered scope:
1. Model quality: the open findings [[F-008 No model beats the base rate on held-out years]], [[F-009 Separate horizon models can contradict each other]], [[F-011 Forecast intervals under-cover]], [[F-012 Recession model lowers risk when unemployment rises]], [[F-013 Replays show most recessions were missed]].
2. Data: OECD and World Bank connectors ([[F-002 OECD CLI missing for Belgium and Netherlands]], [[F-004 World Bank central-government debt is sparse]]); ALFRED vintages with a `FRED_API_KEY` for true point-in-time US replays.
3. Countries: UK, IT, ES, PL, RO, EA only after their series are mapped and validated.
