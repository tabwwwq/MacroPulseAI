---
type: status
phase: 10
phase_name: Hardening & release (complete)
updated: 2026-11-12
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
- 🕰️ **ALFRED vintages (US)** (2026-11-12): `vintages-sync`, `/api/vintages/revisions`, *first release vs today* card on the US tabs; a 2022 technical recession by first release was revised away ([[F-017 ALFRED shows a 2022 technical recession that was revised away]]). CI: run 43215886807 for `b9edade` passed all five jobs. The first two runs (`59d5005`, `0b045b4`) failed only at Lint: a Python block in a brief needed formatting, then an import order a stale local ruff cache had hidden.
- 🧠 **Vintage replay + neural network** (2026-11-12): US replays re-fit the stored fold model, check it reproduces the stored estimate, then score it on GDP, CPI and unemployment as first published ([[ADR-0025 Vintage replay re-fits the stored fold model]]); real-time data hid the 2008 downturn and amplified the 2022 false alarm ([[F-018 First-release figures hid the 2008 downturn and amplified the 2022 false alarm]]). A small MLP joined the candidates and is now published for 4 quarters by the development-only rule, still without held-out skill ([[ADR-0026 Small neural network as a walk-forward candidate]], [[F-019 The neural network wins H=4 by a small margin and reacts strongly to inflation acceleration]]). Local model wrote `vintage_series` and the card. CI: run 43246114198 for `16409af` passed all five jobs on the first try.
- 📈 **OECD connector** (2026-11-12): composite leading indicator for DE, FR, US and composite business / consumer confidence for all five countries as separate indicators (13 series, 9,375 observations, "4/5 sources synced"); per-host throttling after an OECD rate limit ([[ADR-0027 OECD connector with confidence indicators kept apart from the CLI]], [[F-020 OECD rate-limits anonymous syncs within a minute]]). Line charts now fit the data instead of forcing zero. Local model wrote the connector. CI run 43264272331 for `061dcce` failed at the demo step: the snapshot predates the OECD series ([[F-021 Demo load failed on series registered after the snapshot]]); fixed in `c7ab379`; CI run 43266164427 passed all five jobs.
- All ten roadmap phases are complete. CI: run 43023762417 for `0dde5a0` passed all five jobs — API, Web, Security audit (history/tree secret scan, pip-audit, pnpm audit), E2E (58 Playwright on the demo snapshot) and the Docker compose stack on PostgreSQL. The previous run 43022549543 (`31ba843`) failed only the security scan on this phase's own fake test credentials; reviewed and allowlisted in `0dde5a0`.

## Working (verified 2026-11-11)
- Data: 44 native series (31 Eurostat / ECB / FRED + 13 OECD), 35,077 observations; BE/DE/FR/NL `full`, US `partial`. The 2026-11-09 rows (without OECD) ship as the demo snapshot `data/demo/snapshot-2026-11-09.json.gz` (`pnpm demo`, DEMO banner).
- Models: H=2 HistGradientBoosting, H=4 neural network (MLP, since run `20261112T150103Z`; before: Logistic Regression); artifacts in `models/artifacts` (ignored); training takes ~12 s.
- API: all endpoints of CLAUDE.md §9 except admin sync/train (CLI only, by design); 64 KiB body limit, security headers, credential redaction in stored provenance.
- Web: all ten pages on the refreshed design; production CSP; axe WCAG A/AA clean at 1440 px and 375 px (58/58 after the refresh); shell-shared queries are hydration-safe ([[F-016 Hydration mismatch from queries shared with the shell]]).
- Checks (2026-11-12): 371 pytest (+1 PostgreSQL in CI, +22 live; OECD live 6/6), 149 Vitest, ruff, mypy `--strict`, ESLint, tsc, `next build`, 70 Playwright, `pnpm smoke` 2981/2981; earlier also secret scan, `pip-audit`, `pnpm audit`.
- Clean clone: fresh `git clone` of `75c88b5` → bootstrap 3 min 28 s, demo load 6.6 s, train 12.8 s; 283 pytest, 104 Vitest, lint, build, smoke 2883/2883 all passed.
- Local model: llama.cpp Vulkan b12259 + Qwen3.8-27B Q3_K_XL outside the repo; `docs/LOCAL_MODEL.md`.

## Blockers & risks
- [[F-008 No model beats the base rate on held-out years]] — shown next to every probability.
- [[F-009 Separate horizon models can contradict each other]] — flagged in the UI, not resolved.
- [[F-011 Forecast intervals under-cover]] — coverage shown and flagged, method unchanged.
- [[F-012 Recession model lowers risk when unemployment rises]] — visible in the scenario lab, not tuned away.
- [[F-013 Replays show most recessions were missed]] — 2Q warned 0 / 20, 4Q 6 / 22; listed per recession on `/history`.
- [[F-006 US October 2025 observations missing]] — handled by the one-month staleness rule.
- [[F-002 OECD CLI missing for Belgium and Netherlands]] — mitigated: BE/NL show composite confidence as separate indicators; no CLI exists for them.
- Models are trained on revised data; US replays additionally show the estimate on the figures as first published (since 2026-11-12), the main replay stays a revised-data approximation. US ALFRED vintages of GDP, CPI and unemployment are stored and shown as *first release vs today* since 2026-11-12 ([[ADR-0024 ALFRED vintages in separate tables with a first-release window]]); US stays `partial` (series metadata still not fetched).
- [[F-007 OneDrive locks the virtual environment]] — also stale dev-server reloads; restart servers after edits.
- Docker not installed locally: the compose stack is verified in CI only.

## Next
Release work is finished; remaining items are improvements, not gaps in the delivered scope:
1. Model quality: [[F-019 The neural network wins H=4 by a small margin and reacts strongly to inflation acceleration]] (seed averaging / monotonic constraints, pre-registered) and the open findings [[F-008 No model beats the base rate on held-out years]], [[F-009 Separate horizon models can contradict each other]], [[F-011 Forecast intervals under-cover]], [[F-012 Recession model lowers risk when unemployment rises]], [[F-013 Replays show most recessions were missed]].
2. Data: World Bank connector ([[F-004 World Bank central-government debt is sparse]]); OECD indicators as pre-registered model features; training and labels on first-release US data (replays already use it).
3. Countries: UK, IT, ES, PL, RO, EA only after their series are mapped and validated.
