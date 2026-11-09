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

**Status:** Planned; no trained model or measured model metrics are claimed.
**Goal:** Reproduce technical-recession labels and horizon-safe temporal backtests.
**Deliverables:** H=2/4 labels, as-of feature snapshots, lag/vintage documentation,
prevalence baseline, Logistic Regression, an available boosted-tree challenger and artifacts.

Acceptance criteria:

- [ ] Tests establish that an event requires two consecutive negative real GDP q/q quarters entirely within the next H quarters; zero is not negative.
- [ ] Missing GDP and incomplete future horizons produce excluded/censored labels, never false negatives; event/window dates are documented and tested.
- [ ] Feature eligibility uses publication/vintage evidence or explicit conservative lag assumptions; annual inputs use already-published observations with staleness flags.
- [ ] Walk-forward/expanding splits have horizon-safe purge/gaps and pooled-country temporal isolation; leakage tests show preprocessing fits only on training data.
- [ ] Run prevalence baseline and Logistic Regression; execute a boosted-tree challenger only if installed, recording any unavailable dependency.
- [ ] Report measured Brier, log loss, ROC/PR-AUC where defined, calibration, precision/recall, threshold and real sample/event counts; undefined metrics show N/A with reason.
- [ ] Calibration uses disjoint temporal data when supported; final test data stays held out.
- [ ] Save reproducible artifacts with cutoff, dataset snapshot, feature/target versions, command/seed, model version and evaluation method; keep NBER reference separate.

## Phase 6 — Explainable risk dashboard and model laboratory

**Status:** Planned; `/recession` and `/lab` are not-built routes.
**Goal:** Expose actual evaluated inference and transparent diagnostics.
**Deliverables:** Inference/model APIs, horizon selector, risk timeline, explanation charts,
split/calibration/ROC/PR views, baseline comparison and reproducibility card.

Acceptance criteria:

- [ ] Demonstrate one inference round-trip from stored data and saved artifact to displayed probability, with model version, as-of date, prediction timestamp, freshness and coverage.
- [ ] 2Q/4Q selection requests the corresponding target/model; unsupported countries/horizons are covered by validation tests.
- [ ] Missing model/data/metrics return actionable unavailable states and no invented probability.
- [ ] Explanations use working SHAP or a documented coefficient/permutation fallback; risk categories and uncertainty limits are explained.
- [ ] Lab displays actual baseline/model metrics, sample/event counts, temporal splits, thresholded confusion matrix and N/A for undefined curves/metrics.
- [ ] Reproducibility card includes command, seed, snapshot, version and code revision when known; UI/API tests and build pass.

## Phase 7 — Forecasts and scenario simulator

**Status:** Planned; `/forecasts` and `/scenarios` are not-built routes.
**Goal:** Provide evaluated indicator forecasts and bounded non-causal sensitivity analysis.
**Deliverables:** GDP growth/inflation/unemployment forecasts, naive baselines and stronger
challenger, rolling backtests, empirical intervals and functional scenario controls.

Acceptance criteria:

- [ ] Run reproducible rolling backtests for supported forecast series; show actual errors and baseline comparisons or explicit insufficiency reasons.
- [ ] Forecasts distinguish actuals/projections and use documented, empirically tested intervals with stated assumptions.
- [ ] Scenario inputs are validated/bounded, requests debounced, and slider changes alter real model calculations with baseline/delta shown.
- [ ] Display “Exploratory model sensitivity analysis, not a causal economic simulation” and out-of-distribution/unsupported-combination warnings.
- [ ] Reset/save/export actions work and preserve country/as-of/model context; unavailable calculations stay unavailable.
- [ ] Demonstrate one complete forecast/scenario interaction; API/UI tests and build pass.

## Phase 8 — Historical Crisis Time Machine

**Status:** Planned; `/history` is a not-built route.
**Goal:** Replay eligible historical information without future-data or future-training leakage.
**Deliverables:** Time scrubber, known-at-date panel, predicted versus subsequently realized
events, misses/false alarms, ALFRED vintages where verified and European approximation labels.

Acceptance criteria:

- [ ] Temporal tests exclude features and model-training outcomes unavailable at the replay date.
- [ ] Verify ALFRED vintage/release access using server-side credentials before claiming true US point-in-time replay.
- [ ] European/latest-revision replay prominently states “revised-data / release-lag approximation”; document exact lag assumptions and missing vintage evidence.
- [ ] Scrubber changes eligible inputs and outputs; realized outcomes are clearly subsequent observations, separate from NBER reference dates.
- [ ] Show traceable event markers and actual false-positive/false-negative examples where evaluable; insufficient history produces unavailable state.
- [ ] Temporal-leakage tests, replay API/UI checks and build pass.

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
