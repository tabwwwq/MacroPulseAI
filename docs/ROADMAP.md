# Roadmap

Snapshot: 2026-11-08. Follow [CLAUDE.md](../CLAUDE.md) and the ten named prompts in
[MACROPULSE_PHASE_PROMPTS.md](../MACROPULSE_PHASE_PROMPTS.md). Their detailed phase
numbering expands the specification's build order: foundation → connectors/storage/quality
→ dashboards → recession models → forecasts/explanations → scenarios/replay → reporting
→ release hardening. [ARCHITECTURE.md](ARCHITECTURE.md) distinguishes existing and planned parts.

Only Phase 1 verification explicitly supplied by the lead engineer is checked below.
Those checks were run locally on Windows 11 on 2026-11-08, not rerun by this documentation
task. An unchecked item is an outstanding acceptance gate, even if scaffolding exists.
Docker is not installed locally; compose/images are written but unverified, with CI builds intended.

## Phase 1 — Product blueprint and repository setup

**Status:** Implemented and locally verified per lead engineer; container execution unverified.
**Goal:** Establish the monorepo and a working design shell with truthful API state.
**Deliverables:** Next.js/FastAPI foundation, registry/schema/migrations, typed contract,
design tokens, navigation, setup workflow, architecture and feasibility documentation,
PostgreSQL compose configuration and smoke tests.

Acceptance criteria:

- [x] Backend suite passes: 27 pytest tests, as reported by the lead.
- [x] Backend ruff lint, ruff format check and `mypy --strict` are clean, as reported by the lead.
- [x] Frontend TypeScript and ESLint checks are clean, as reported by the lead.
- [x] Frontend suite passes: 16 Vitest tests, as reported by the lead.
- [x] `next build` succeeds with 12 routes, as reported by the lead.
- [x] Manual browser checks pass for navigation, country switcher and mobile drawer.
- [x] Manual API-offline and retry-state checks pass.
- [ ] Independently replay documented clone/setup workflow on a clean machine.
- [ ] Run `docker compose up --build`; verify migrations, PostgreSQL and service readiness.

## Phase 2 — Production-grade UI system

**Status:** Done 2026-11-09 — verified locally (see vault `20 Phases/Phase 02`).
**Goal:** Complete consistent responsive layouts and functional controls without fake data.
**Deliverables:** Sidebar/topbar, country/as-of selection, chart wrappers, KPI cards,
tooltips, skeletons, stale/missing/error states and mobile layouts.

Acceptance criteria:

- [x] All module layouts use shared tokens/components and typed queries; unbuilt features show explicit unavailable/not-built states.
- [x] Keyboard traversal, focus handling and screen-reader names work for shell, selectors, tooltips and mobile menu.
- [x] Country/as-of selectors and every enabled filter/button change visible state; unavailable actions are disabled with reasons or omitted.
- [x] Loading, empty, stale, API-error and retry states are exercised with deterministic fixtures.
- [x] Inspect desktop/tablet/mobile layouts for overflow and reduced motion; record screenshots when supported.
- [x] Frontend tests, lint/type checks and production build pass after UI changes.

## Phase 3 — Economic data ingestion and metadata

**Status:** ✅ Complete (2026-11-09). Live `data-sync` stored **21,094 observations** from 24 native
series (Eurostat 16 · 4,417 rows, ECB 1 · 69 rows, FRED 7 · 16,608 rows); all three runs succeeded and a
re-run is idempotent. Computed support: BE, DE, FR, NL `full`; US `partial` (FRED metadata needs an API key).
**Goal:** Retrieve and store genuine official observations with provenance and quality checks.
**Deliverables:** At least two verified official adapters beginning with Eurostat GDP and
another feasible Eurostat indicator; ECB/FRED as practical; normalized storage, registry,
quality checks, `data-sync` CLI and source-health API backed by actual runs.

Acceptance criteria:

- [x] Live-verify at least two adapters; report exact keys, returned row counts and failures without substituting invented values. *(Eurostat, ECB and FRED; per-series rows and quality warnings printed by `data-sync` and recorded in `quality_checks`.)*
- [x] Store country/metric/period/value, unit, frequency, adjustment, source URL/key, retrieval time and known publication/vintage dates; unknown dates stay null. *(The dataset `updated` stamp is kept as `source_updated_at`; these endpoints give no per-observation publication date or vintage, so none is stored.)*
- [x] Deterministic tests cover response validation, pagination where needed, timeouts/backoff, rate limits, resumable/idempotent upserts and partial failures. *(Real captured fixtures; `httpx.MockTransport` for 5xx backoff, 429 `Retry-After`, no retry on 4xx and transport errors. Pagination is not needed: each endpoint returns a whole series per request.)*
- [x] Transform tests reject gaps/nonadjacent GDP quarters, incompatible units and invalid frequency alignment; missing official values remain null with reasons. *(Growth only across adjacent published periods; multi-series/multi-unit responses are rejected; FRED dates that are not period starts are rejected; FRED `.` values are skipped and counted.)*
- [x] `data-sync` records run status/counts/errors; source-health API distinguishes never-synced, success, degraded and failed, with actual last successful fetch time.
- [x] Resolve or explicitly retain the country/source blockers below; no country reaches full on stale or unvalidated core series. *(HICP successor `prc_hicp_minr` verified; OECD CLI and the FRED key path retained as blockers.)*
- [x] Verify httpx/certifi TLS on Windows; keep live API checks separate from deterministic default CI tests. *(Live sync on Windows 11; `pytest -m live` runs only with `MACROPULSE_LIVE_TESTS=1`.)*

## Phase 4 — Data coverage and actual dashboards

**Status:** ✅ Complete (2026-11-09). Overview, Country Explorer, Compare and Data Observatory plot the
21,094 stored official observations with provenance; new endpoints `/api/countries/{iso2}/summary`,
`/api/countries/{iso2}/data-quality`, `/api/data-quality` and `/api/observations/export`; `pnpm smoke`
passes 348/348 checks against the synced database.
**Goal:** Make Overview, Country Explorer, Compare and Data Observatory useful with actual data.
**Deliverables:** Indicator/summary/quality APIs, sourced KPIs/charts, aligned comparisons,
coverage matrix, source health, date filters, history tables and CSV export.

Acceptance criteria:

- [x] All four pages render stored official observations and show explicit empty/error states when absent. *(404 "not published" and 503 "not synced" are empty states with the API's reason, never errors or zeros.)*
- [x] Country/date selections alter returned and displayed data; comparisons allow up to four countries and reject or explain incompatible definitions/units/spans. *(As-of quarter cuts periods server-side; history window 5Y/10Y/20Y/Max; spread mode is refused for mixed native frequencies.)*
- [x] Each KPI/chart exposes source, transformation, unit, adjustment, reference period, retrieval time and known publication date; shared ECB rates are labeled shared. *(Per-observation publication dates are not offered by these APIs; the dataset update stamp is shown as "source updated".)*
- [x] BE/DE/FR/NL/US support is computed from validated stored coverage; full/partial/unavailable includes a reason. *(BE/DE/FR/NL full, US partial — FRED metadata needs the key-based API.)*
- [x] Freshness and observation age are distinct; stale and missing observations appear in the coverage/quality views. *(KPI: days since period end vs last fetch; lineage table: latest checks incl. gaps and failed attempts.)*
- [x] CSV exports match the displayed selection and retain citations/units/dates; chart controls visibly work. *(Chart CSV headers carry unit + citation; raw CSV carries per-row source URL, retrieval time and attribution.)*
- [x] End-to-end smoke tests for all four pages and frontend build pass. *(`pnpm smoke` automates the API side; the four pages were checked in a browser at 1440 px and 375 px. No browser-automation suite yet.)*

## Phase 5 — Recession target, time-aware features and first real model

**Status:** ✅ Complete (2026-11-09) — with an honest, weak result. `uv run macropulse train` builds 712
as-of rows (5 countries, US from 1955, EU from 2000), runs a yearly walk-forward backtest per horizon and
stores every model's metrics and predictions. Published (chosen on 2000–2014 development Brier only):
H=2 HistGradientBoosting, Brier skill vs prevalence **+0.099** on development but **−0.448** on held-out
2015–2026; H=4 Logistic Regression, **+0.032** development and **−0.754** held-out. **No model beats the
historical base rate on the held-out years** (COVID-2020 is not forecastable from these inputs; 2022–24
curve inversion gave false alarms for BE/FR/US) — see finding F-008. The UI states this.
**Goal:** Reproduce technical-recession labels and horizon-safe temporal backtests.
**Deliverables:** H=2/4 labels, as-of feature snapshots, lag/vintage documentation,
prevalence baseline, Logistic Regression, an available boosted-tree challenger and artifacts.

Acceptance criteria:

- [x] Tests establish that an event requires two consecutive negative real GDP q/q quarters entirely within the next H quarters; zero is not negative. *(`packages/ml/tests/test_target.py`, incl. the methodology table.)*
- [x] Missing GDP and incomplete future horizons produce excluded/censored labels, never false negatives; event/window dates are documented and tested. *(Real run: H=2 702 observed / 10 censored; H=4 692 / 20. Technical recessions found in the data are printed by `train` and stored in each artifact's metadata.)*
- [x] Feature eligibility uses publication/vintage evidence or explicit conservative lag assumptions; annual inputs use already-published observations with staleness flags. *(Conservative lags in days after period end: GDP 60, inflation 30, unemployment 45, rates 30, ECB 0, FEDFUNDS 7; one missing month falls back with a staleness flag, two exclude the row. No annual inputs are used.)*
- [x] Walk-forward/expanding splits have horizon-safe purge/gaps and pooled-country temporal isolation; leakage tests show preprocessing fits only on training data. *(Training labels must end before the first test quarter; poisoned-future and scaler-fit tests.)*
- [x] Run prevalence baseline and Logistic Regression; execute a boosted-tree challenger only if installed, recording any unavailable dependency. *(HistGradientBoosting ± temporal Platt calibration ran; XGBoost is an optional extra and is recorded as "not installed".)*
- [x] Report measured Brier, log loss, ROC/PR-AUC where defined, calibration, precision/recall, threshold and real sample/event counts; undefined metrics show N/A with reason. *(Per split and per country, stored in `model_metrics`; threshold 0.5.)*
- [x] Calibration uses disjoint temporal data when supported; final test data stays held out. *(Platt calibration on the latest 30 % of each training window behind a purge gap, only with ≥ 6 events of each class; 2015+ never used for selection. Held-out results of the first run were seen before the term spread was added — recorded in F-008.)*
- [x] Save reproducible artifacts with cutoff, dataset snapshot, feature/target versions, command/seed, model version and evaluation method; keep NBER reference separate. *(`models/artifacts/<run>/h<H>/model.joblib + metadata.json`; `model_versions` rows; NBER is excluded from features and target.)*

## Phase 6 — Explainable risk dashboard and model laboratory

**Status:** ✅ Complete (2026-11-09). `/recession` serves live inference from stored data and the saved artifact
(round trip verified for 5 countries × 2 horizons by `pnpm smoke`, 495/495 checks); `/lab` shows every model of the
latest run with measured out-of-sample metrics. Both state that the published models do not beat the base rate on
the 2015+ held-out years.
**Goal:** Expose actual evaluated inference and transparent diagnostics.
**Deliverables:** Inference/model APIs, horizon selector, risk timeline, explanation charts,
split/calibration/ROC/PR views, baseline comparison and reproducibility card.

Acceptance criteria:

- [x] Demonstrate one inference round-trip from stored data and saved artifact to displayed probability, with model version, as-of date, prediction timestamp, freshness and coverage. *(`GET /api/recession/predict` rebuilds the as-of snapshot, loads the joblib artifact (only from `models_dir`) and returns the probability with all of these; the recomputed value equals the one stored at training for every country and horizon.)*
- [x] 2Q/4Q selection requests the corresponding target/model; unsupported countries/horizons are covered by validation tests. *(`unsupported_country`, `unsupported_horizon`, `invalid_as_of`, `features_unavailable` tested.)*
- [x] Missing model/data/metrics return actionable unavailable states and no invented probability. *(`model_not_trained`, `model_artifact_missing`, `model_artifact_untrusted`, `model_incompatible` → 503 with the CLI hint; the UI shows "Model not trained".)*
- [x] Explanations use working SHAP or a documented coefficient/permutation fallback; risk categories and uncertainty limits are explained. *(SHAP is not installed: exact additive log-odds contributions for logistic, local sensitivity to the training mean for trees; fixed bands < 15/30/50 %; no interval, with the reason stated; a P(4Q) < P(2Q) contradiction between the separate horizon models is flagged.)*
- [x] Lab displays actual baseline/model metrics, sample/event counts, temporal splits, thresholded confusion matrix and N/A for undefined curves/metrics.
- [x] Reproducibility card includes command, seed, snapshot, version and code revision when known; UI/API tests and build pass. *(185 pytest, 79 Vitest, `next build`.)*

## Phase 7 — Forecasts and scenario simulator

**Status:** ✅ Complete (2026-11-10). `/forecasts` serves rolling-origin backtested forecasts of real GDP growth,
inflation and unemployment for all 15 country/indicator series; `/scenarios` re-scores the published recession
model under bounded input shocks. `pnpm smoke`: 2105/2105 checks, including every forecast series and a scenario
round trip for 5 countries × 2 horizons. Result stated plainly: the 80 % intervals **under-cover** (median measured
coverage 74 % one quarter ahead, 71 % at eight quarters, 50 % at worst) and the AR challenger beats the naive
forecast one quarter ahead for only 8 of 15 series.
**Goal:** Provide evaluated indicator forecasts and bounded non-causal sensitivity analysis.
**Deliverables:** GDP growth/inflation/unemployment forecasts, naive baselines and stronger
challenger, rolling backtests, empirical intervals and functional scenario controls.

Acceptance criteria:

- [x] Run reproducible rolling backtests for supported forecast series; show actual errors and baseline comparisons or explicit insufficiency reasons. *(`packages/ml/forecast.py`: naive, rolling mean and a direct ridge AR refitted at every origin on data known then; MAE, RMSE, RMSE vs naive on common origins, bias and coverage per horizon; fewer than 20 scored errors → N/A with the reason; 404 `forecast_unavailable` when history is too short. Deterministic, no random state.)*
- [x] Forecasts distinguish actuals/projections and use documented, empirically tested intervals with stated assumptions. *(Solid published history, dashed projection, 80 % ribbon from the 10th/90th percentiles of the model's own past errors; coverage is measured with intervals built only from errors already known at each origin, shown per horizon and flagged "under" when > 10 points below nominal; assumptions listed on the page and in the API.)*
- [x] Scenario inputs are validated/bounded, requests debounced, and slider changes alter real model calculations with baseline/delta shown. *(Pydantic bounds with `extra="forbid"`; 350 ms debounce; the published artifact scores baseline and shocked inputs; documented mechanical mapping per shock.)*
- [x] Display “Exploratory model sensitivity analysis, not a causal economic simulation” and out-of-distribution/unsupported-combination warnings. *(Banner on the page and `disclaimer` in every response; per-input training min/max and 5–95 % flags; joint squared-Mahalanobis check against the training covariance with a χ²(11) 99 % line.)*
- [x] Reset/save/export actions work and preserve country/as-of/model context; unavailable calculations stay unavailable. *(Shocks, horizon, country and as-of in the URL; saved scenarios in this browser's localStorage with model version; JSON export with request, result and disclaimer; untrained horizon → 503 "Model not available".)*
- [x] Demonstrate one complete forecast/scenario interaction; API/UI tests and build pass. *(Browser: DE/US/FR/BE forecasts incl. US unemployment as of 2019-Q4 against the COVID spike; NL 2Q scenario GDP −1.5 pp, unemployment +2 pp: 2.3 % → 20.6 %, saved, reloaded, loaded, reset, deleted. 217 pytest, 92 Vitest, `next build`.)*

## Phase 8 — Historical Crisis Time Machine

**Status:** ✅ Complete (2026-11-10). `/history` replays any quarter with a walk-forward estimate (2000-Q1 or 2002-Q1
onwards, by horizon) for all five countries: the estimate of the fold model fitted only on outcomes published before
that year, the inputs as known at the cut-off, the outcome window as published later, and every realised recession
marked warned / missed / not evaluable plus every false alarm. `pnpm smoke`: 2818/2818 checks including 40 crisis
replays. Result stated plainly: the 2-quarter model warned in the quarter before onset for **0 of 20** evaluable
recessions; the 4-quarter model for **6 of 22**, with 26 false-alarm episodes (10 right after a recession).
**Goal:** Replay eligible historical information without future-data or future-training leakage.
**Deliverables:** Time scrubber, known-at-date panel, predicted versus subsequently realized
events, misses/false alarms, ALFRED vintages where verified and European approximation labels.

Acceptance criteria:

- [x] Temporal tests exclude features and model-training outcomes unavailable at the replay date. *(`packages/ml/tests/test_replay_leakage.py`: deleting every observation published after the replay date — inputs and the outcomes later models learn from — reproduces the walk-forward probability of every model exactly; every training outcome of a fold was published by its first test quarter. A mutation without the horizon purge is detected.)*
- [x] Verify ALFRED vintage/release access using server-side credentials before claiming true US point-in-time replay. *(Not claimed: `FRED_API_KEY` is not configured, so ALFRED could not be verified and vintage replay is not implemented; the US banner says so and US replays are labelled approximations like the European ones.)*
- [x] European/latest-revision replay prominently states “revised-data / release-lag approximation”; document exact lag assumptions and missing vintage evidence. *(Banner, page badge and API `basis` with the lag table: GDP 60 d, inflation 30 d, unemployment 45 d, ECB decisions 0 d, FEDFUNDS 7 d, monthly rates 30 d; Eurostat/ECB serve latest revisions only.)*
- [x] Scrubber changes eligible inputs and outputs; realized outcomes are clearly subsequent observations, separate from NBER reference dates. *(Scrubber, presets and episode links set the as-of in the URL; "Published by" vs "Published later" GDP; NBER months in a separate, labelled US box.)*
- [x] Show traceable event markers and actual false-positive/false-negative examples where evaluable; insufficient history produces unavailable state. *(Each recession and false alarm links to its replay; recessions before the first fold are "not evaluable"; replays before it return 404 `replay_unavailable` with the reason.)*
- [x] Temporal-leakage tests, replay API/UI checks and build pass. *(234 pytest, 97 Vitest, `next build`; browser: presets, scrubber, horizon switch, episode links, unavailable state, 375 px.)*

## Phase 9 — Analyst-grade PDF reports

**Status:** Planned; `/reports` is a not-built route.
**Goal:** Export readable, dated reports with verifiable analytical content.
**Deliverables:** PDF download, selected country/as-of indicators and charts, available
model/forecast results, source citations, limitations, rules-based summary and CSV export.

Acceptance criteria:

- [ ] Generated PDF opens and is visually inspected; tables/charts match the selected country/as-of and actual stored results.
- [ ] Include units, source URLs, retrieval/publication dates where known, model/version/horizons, methodology and uncertainty/vintage caveats.
- [ ] Missing observations or untrained models are labeled; summary uses recorded metrics/rules without invented analysis.
- [ ] Download has a descriptive filename; generation failures produce safe server errors and no credentials appear in exports/logs.
- [ ] CSV matches underlying chart data with citations and dates; export tests and frontend build pass.

## Phase 10 — Production hardening, audit and GitHub-ready release

**Status:** Planned; local Phase 1 checks are not a release audit.
**Goal:** Verify reproducible setup, deployment, security, accessibility and truthful release documentation.
**Deliverables:** Full audit/fixes, CI, realistic E2E/smoke tests, verified containers/deploy
guide, README/methodology/limitations and a working/partial/not-implemented inventory.

Acceptance criteria:

- [ ] Run backend/frontend tests, lint/type checks and production build; fix failures and record actual outputs.
- [ ] Run realistic core-page E2E tests on desktop/mobile, keyboard navigation and stale/offline/error paths; fix broken routes/controls and overflow.
- [ ] Execute compose image builds/startup, migrations and PostgreSQL readiness in a Docker-capable environment; document environment and results.
- [ ] Audit secrets/client bundle/history, CORS, validation, query safety, dependencies, logs and export handling; expensive jobs are bounded/restricted before exposure.
- [ ] Clean-clone setup and documented migration/sync/train/test/build/demo commands work; credential-free demo is prominently labeled and uses attributed genuine fixtures.
- [ ] README/deployment guide includes accurate Windows instructions, source attribution, target/methodology, limitations and only real screenshots/measured scores.
- [ ] Publish a truthful working/partly-working/not-implemented table; no release completion claim while major checks fail.

## Country targets and data gates

Evidence: [DATA_FEASIBILITY.md](DATA_FEASIBILITY.md), recorded probe dated 2026-11-08.
Its proposed `partial` levels describe source feasibility, not runtime support. Current
application support remains `unavailable` for every registered country until observations
are ingested. The five initial registry targets are `full`; expansion is conditional.
Full core coverage requires verified, current quarterly real GDP, inflation and unemployment,
plus validated definitions/transforms and actual ingestion. Optional feature gaps must remain explicit.

| Country | Target | Source feasibility / acceptance gate |
|---|---|---|
| Belgium (BE) | full, initial | Partial: GDP through 2026-Q2, unemployment through 2026-09; verify current HICP successor. OECD queried slice has confidence only, no CLI |
| Germany (DE) | full, initial | Partial: GDP through 2026-Q3, unemployment through 2026-09; current HICP required; fix OECD CLI key/variant and verify history |
| France (FR) | full, initial | Partial: GDP through 2026-Q3, unemployment through 2026-09; current HICP required; fix OECD CLI key/variant and verify history |
| Netherlands (NL) | full, initial | Partial: GDP through 2026-Q3, unemployment through 2026-09; current HICP required. OECD queried slice has confidence only, no CLI |
| United States (US) | full, initial | Partial: FRED CSV values exist, but units/frequency/adjustment and inflation transformation require API metadata validation; ALFRED/release dates unverified |
| Euro Area (EA) | Conditional expansion, no full commitment | Partial feasibility: GDP aggregate key unverified, EA20 unemployment response rejected, HICP stale; reconcile aggregate composition with ECB U2 |
| United Kingdom (GB), Italy (IT), Spain (ES), Poland (PL), Romania (RO) | Conditional expansion, no full commitment | Not validated in this probe/initial registry; verify each quarterly GDP target and essential indicator mapping before assigning support |

Phase 3–5 blocking decisions:

- `prc_hicp_manr` ends at **2025-12**, despite its 2026-02-06 update timestamp; it is stale and possibly discontinued. Discover and verify a current successor before claiming current inflation or European full support.
- BE/NL OECD slices contain `BCICP`/`CCICP`, not `LI`. Do not relabel confidence as CLI. DE/FR/US CLI slices do not establish fixed keys or training history. Missing CLI blocks that feature, not core full support if validated core series suffice; choose a documented reduced feature set or retain partial model coverage.
- FRED CSV probes leave official metadata null. Server-side `FRED_API_KEY` validation is required for metadata/ALFRED paths; credentials/vintages were not probed. US full support waits for core-series validation; true vintage replay additionally waits for ALFRED evidence.
- Eurostat GDP levels require validated adjacent-quarter q/q transforms. Latest revisions are not historical vintages; retrieval/update timestamps are not publication dates. Research conservative release lags before as-of training/replay.
- ECB rates are event-dated shared euro area rates, requiring explicit calendar alignment. Annual World Bank GDP cannot replace the quarterly target; sparse central-government debt cannot be spliced with quarterly general-government or US federal debt.
- Probe success does not establish licensing compliance, scheduled refreshes, robust connectors or model readiness. Live verification is owned by the lead engineer; delegated Codex sandbox lacks network and per-user Python.

## Definition of done

The final product must satisfy CLAUDE.md's definition, beyond the Phase 1 foundation:

- [ ] A clean clone runs through documented setup and opens a responsive app with working navigation on all completed pages.
- [ ] Users browse real sourced historical macro data and verify provenance, transformations, freshness and coverage.
- [ ] At least one genuine training/backtesting pipeline is reproducible, with leakage/censoring tests, measured metrics and a justified probability estimate or explicit untrained/unavailable state.
- [ ] Users download a source-cited report with dates, methodology and uncertainty notes.
- [ ] Tests and production build pass; setup/deployment limitations are explicit.
- [ ] No hidden fake numbers, broken enabled controls, fabricated accuracy or train/test leakage remains; demo, predictions, historical statistics and non-causal scenarios are clearly distinguished.
