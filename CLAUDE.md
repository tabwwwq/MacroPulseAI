# MacroPulse AI — Repository Instructions for Claude Code

You are an autonomous senior engineering team: staff full-stack developer, lead data engineer, applied ML scientist, financial economist, product designer, QA engineer, security engineer, and DevOps lead. Build a stunning, functional, professional, portfolio-grade web application called **MacroPulse AI**.

Do not deliver wireframes, a static landing page, a toy Streamlit demo, fabricated financial data, mock APIs pretending to be live, or a collection of non-functional placeholders. Deliver a working, documented monorepo that I can run locally, test, deploy, and publish to GitHub. Use modern, maintainable code, robust error handling, accessible UI, credible modeling, and beautiful design. Prioritize engineering truth over flashy claims. Never claim a model has been trained, data has synced, or an API works without executing and verifying it. When network/API/credentials are unavailable, build a clearly labeled demo/offline path and explain what remains unverified.

## 1. Mission and positioning

MacroPulse AI is a macroeconomic intelligence and recession early-warning platform for financial analysts, consulting teams, research students, and risk professionals. The user can:
- Monitor the economic health of supported countries.
- Explore actual historical GDP, inflation, unemployment, policy rates, debt and other macroeconomic series.
- Compare countries on genuinely comparable units, time spans and definitions.
- Inspect transparent, probabilistic estimates of future *technical recession* risk for the next 2 and 4 quarters, with model/version/date and explicit uncertainty.
- Forecast selected economic indicators with honest uncertainty intervals.
- Run illustrative, non-causal scenario sensitivity analyses.
- Replay past crises using only the information a model could have had at the chosen as-of date (or explicitly marked proxies when true vintage data is unavailable).
- Explore model performance, calibration, explanations, training history, data quality, and limitations.
- Export professional reports with sources, timestamps and methodological notes.

Be precise: an official recession designation is not the same as a technical recession defined by two consecutive negative quarter-over-quarter real GDP growth readings. NBER official US recession dates may be displayed separately as an external reference, but must never be mislabeled as the same training target as GDP-based technical recessions. All predictions are analytical estimates, not factual declarations or investment advice.

## 2. Technology and architecture

Build a pnpm + Python monorepo:
- `apps/web`: Next.js App Router, React, TypeScript strict mode, Tailwind CSS, shadcn/ui (or equivalent accessible primitives), TanStack Query, ECharts or Plotly for dense responsive financial charts, Lucide icons, tasteful motion (Framer Motion optional).
- `apps/api`: FastAPI, Python 3.12+, Pydantic v2, SQLAlchemy 2, Alembic, pandas, NumPy, scikit-learn, XGBoost when installed, SHAP, httpx, pytest, ruff, mypy where practical. PyTorch LSTM is an optional later benchmark, not a fake requirement.
- PostgreSQL, docker-compose for local use. Redis/background worker only if genuinely needed. Use a simple scheduled job runner or CLI commands first rather than needless infrastructure.
- A clear data science package for connectors, preprocessing, feature engineering, labeling, training, evaluation and inference.
- A typed OpenAPI contract shared or type-generated for the front end.
- Reproducible pinned dependencies and `.env.example`. Secrets only in server environments, never in client code or repository commits.
- CI with GitHub Actions lint, unit/integration tests, backend smoke tests and frontend build.
- A small production deploy guide, Docker support, and Windows PowerShell-friendly setup where feasible.

Suggested layout:
```
apps/
  web/
  api/
packages/
  economics/
  ml/
  shared-types/
scripts/
data/
  demo/           # small licensed/attributed, clearly DEMO fixtures
  processed/      # ignored generated data
models/            # ignored weights / versioned metadata
infra/
tests/
docs/
.github/workflows/
README.md
.env.example
compose.yml
```
Adjust the layout when useful, but keep it coherent and avoid busywork files.

## 3. Countries and scope management

Initial **fully functional** countries: Belgium (BE), Germany (DE), France (FR), Netherlands (NL), USA (US). Attempt UK (GB), Italy (IT), Spain (ES), Poland (PL), Romania (RO), and Euro Area (EA) afterwards only if indicators and definitions are actually mapped and validated. Do not advertise countries as fully supported if the essential GDP target or indicators cannot be retrieved. Show per-country support level: `full`, `partial`, `unavailable`. For the US you may support NBER reference shading from FRED `USREC`, always separately labeled.

The UI must clearly distinguish (a) historical statistics, (b) latest published data, (c) trained model predictions, (d) exploratory sensitivity simulations, (e) demo/sample data.

## 4. Verified source families and connector quality

Build source adapters and dataset-registry entries (dataset code, geographies, frequency, unit, adjustment, release date if known, observations status, last successful sync, source URL):
- Eurostat REST JSON-stat / SDMX for European GDP and related indicators; verified starting dataset `namq_10_gdp` for quarterly GDP. Discover and validate all other dataset codes and dimension filters from official metadata; never invent them.
- European Central Bank Data Portal REST / SDMX 2.1 for policy rates and monetary indicators. Euro Area policy rate is a **shared Euro Area rate**, not falsely represented as a distinct national central-bank policy rate.
- FRED / ALFRED for US indicators and, when supported, historical observation vintage/real-time data. FRED API keys may be necessary; provide an optional server-side `FRED_API_KEY` setup.
- World Bank Indicators API v2 for long-range and annual structural indicators (including debt if compatible, otherwise use explicit alternate official source). It supports unauthenticated access; do not pretend annual debt updates quarterly.
- OECD SDMX data for cross-country leading indicators and additional series after independently verifying query keys and response parsing.

Official documentation references to put in docs:
https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-introduction
https://data.ecb.europa.eu/help/api/overview
https://fred.stlouisfed.org/docs/api/fred/series_observations.html
https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
https://data-explorer.oecd.org/
https://www.nber.org/research/business-cycle-dating/business-cycle-dating-procedure-frequently-asked-questions

Requirements: HTTP timeout/retries with backoff, response validation, throttling, caching, sensible pagination, rate-limit handling, resumable sync, provenance, unit conversion rules, schema checks, missingness reporting and explicit partial failures. Never silently fill missing official data with made-up numbers. For unauthorized network/API access, indicate disconnected/degraded mode and allow an appropriately labeled offline demo or an import from a genuine cached snapshot with source/date.

## 5. Data model and data quality

Create migrations/entities such as `countries`, `data_sources`, `indicator_definitions`, `observations`, `release_events` (nullable when unknown), `ingestion_runs`, `data_quality_checks`, `feature_snapshots`, `target_labels`, `model_versions`, `model_metrics`, `prediction_runs`, `predictions`, `scenario_runs`, and `report_exports` (adjust if appropriate).

Every observation should ideally track country, metric, observation period, value, unit, frequency, seasonal adjustment, original source, dataset key, retrieval time, period availability/first publication time if known, vintage/revision identifier where supported, and quality flags. Model artifacts must identify training cutoff, feature set version, target definition, sample counts and evaluation methodology.

When mixing monthly, quarterly and annual data, normalize to a transparent quarterly `as_of` feature snapshot: do not leak end-of-quarter values that had not been published. Prefer timestamped as-of joins where release dates/vintages exist. If historic vintages are unavailable (Eurostat commonly serves the latest revisions), explicitly label historical simulations as **revised-data / release-lag approximation** rather than true historical point-in-time accuracy. Research and document conservative release-lag assumptions; don't silently assume perfect knowledge at quarter end. Annual data: use the latest *already published* annual observation, with a staleness marker. Implement date-alignment, missing-value and frequency unit tests.

## 6. Exact ML question and labeling

Primary output: **estimated probability of a technical recession in the next 2 quarters** and **in the next 4 quarters**, at an explicitly defined `as_of` date.

For reproducible labels, derive real quarter-over-quarter GDP growth from appropriate comparable seasonally adjusted real GDP series. Define the future event as **at least one pair of consecutive quarters of negative real GDP q/q growth entirely within the next H quarters**, where H = 2 or 4. Explicitly describe target construction, the H-window and event dating. A label is only observable for backtesting after the full future horizon is available; exclude censored/unobservable training labels. A zero GDP growth quarter is not negative. Missing real GDP prevents assigning a trustworthy label. Keep official US NBER recession indicator separate as an external validation layer, not a substitute label.

Use as-of features where possible:
- real GDP q/q and y/y growth, 2- and 4-quarter changes;
- HICP/CPI y/y inflation and recent changes;
- unemployment levels and quarterly change;
- correctly scoped monetary policy rate and rate changes;
- government debt/GDP only if official matching series and publication timing are defensible;
- yield curve slope, leading indicators, industrial production and confidence indices only where clean, compatible historical data is obtainable;
- missingness, staleness and country identifiers where appropriate.

Train models in this order:
1. Non-ML reference baselines: unconditional historical prevalence and simple interpretable threshold / prior-period benchmarks.
2. Logistic Regression with feature scaling and regularization.
3. HistGradientBoosting and/or XGBoost/LightGBM if successfully installed.
4. Calibrate probabilities only on disjoint training/calibration splits, e.g. isotonic or sigmoid calibration when sample counts support it.
5. LSTM/GRU optionally as a research comparison only when a justifiable number of samples and sequences exist; warn when statistically unsuitable. Do not fabricate superiority, and do not ship unused decorative neural-network code.

Avoid random train-test splits for time series, data leakage and fitting scalers/imputers on future data. Use walk-forward/expanding-window splits with fully isolated temporal validation and test sets, a purge/gap appropriate to forward label horizons, and careful treatment of pooled-country temporal overlap. Show small-event and class-imbalance caveats. Expose sample counts and event frequencies. Add confidence bands only when grounded in a documented method; do not call model probability a certainty.

Evaluation: ROC-AUC when defined, PR-AUC, Brier score, log loss, calibration curve, confusion matrix at a transparently chosen threshold, recall/precision and sensitivity by region/time, plus baseline comparison. If only one class occurs in a window, show `N/A` rather than a false metric. Explain why forecast Brier score/calibration matter and why 90% accuracy on mostly non-recession data can be misleading. Keep the test period truly held out. Explain with SHAP when supported or standardized coefficients / permutation importance as honest fallbacks.

For GDP, inflation and unemployment forecasting, start with credible time-series baselines (naive, seasonal naive where appropriate) and a stronger challenger (ARIMA, gradient boosted lag features, etc.) with rolling backtests. Intervals must have a tested/empirical method; mark assumptions. No claims of guaranteed economic predictions.

## 7. Web application — pages and experiences

### A. Landing / Overview (`/`)
Immediate substantive dashboard, not a generic hero-only marketing screen. Slim polished sidebar; top bar with logo, search, country selector, as-of date, light/dark toggle optional, Sync Status. Main screen: top 4-6 KPI tiles (real GDP growth, inflation, unemployment, policy rate, estimated recession risk if an actual trained model is available, data freshness). Large risk timeline with historic downturn shading; smaller inflation/unemployment plots; latest releases timeline; a data-coverage indicator. On first use, show a helpful guided country selector; no fake live numbers.

### B. Country Explorer (`/countries/[code]`)
Deep macro profile with section tabs for Overview, Growth, Prices, Labor, Monetary, Fiscal, Data. Each chart has toggles (line/bar, QoQ/YoY only when meaningful), a date range, data annotations, source tooltip, export CSV/PNG, and clearly labeled seasonality/units. Scrollable history table; missing data messages.

### C. AI Recession Predictor (`/recession`)
Country selector, 2Q/4Q horizon, probability gauge with accurate labels, calibrated risk trend, model name/version, `as_of`, data freshness and coverage confidence. Show contributors via SHAP/permutation, historical outcomes, event definition, methodological limitations and 'Why this probability?' information panel. Never show a fabricated risk number. If no trained artifact: explicit 'Model not trained' state with a CLI instruction or setup action, not a pretend output.

### D. World / Cross-country Compare (`/compare`)
Compare up to 4 supported countries, aligned charts and table: growth, inflation, unemployment, debt where compatible, policy rate coverage, model scores where actually available. Allow selecting period, normalization choices, and consistent baseline. Optional map should honestly indicate unsupported geographies.

### E. Forecast Studio (`/forecasts`)
Multi-step GDP/inflation/unemployment forecasts with historical actual line, projected dashed line, empirical interval ribbon, chosen horizons, model selector, error diagnostics, backtest chart and download. Show N/A rather than inventing values.

### F. Scenario Lab (`/scenarios`)
Interactive sliders for inflation, unemployment, policy rate, GDP growth shocks and optionally debt. Base-versus-scenario forecast risk and feature contribution deltas. Explicit disclaimer: 'Exploratory model sensitivity analysis, not a causal economic simulation.' Show out-of-distribution/unsupported combination warning and feature ranges. Allow saving and exporting scenarios locally or server-side.

### G. Crisis Time Machine (`/history`)
Pick historical as-of date (e.g., around 2007, 2020, 2022) and country. Compare what the model would have predicted using eligible features to realized future GDP recession event. Mark whether the prediction is true point-in-time vintage-backed or revised-data/release-lag approximation. Historical visuals must not imply the model predicted actual events without a valid retrospective evaluation.

### H. ML Laboratory (`/lab`)
Models list, training status, last trained date, training sample count, features, baselines, comparison table, ROC/PR/calibration charts, split timeline, confusion matrix and SHAP explanations. Provide a reproducibility card with training command, seed, git SHA if known, dataset snapshot and model version. Optional admin-only train trigger is fine, but prevent arbitrary unauthenticated training jobs.

### I. Data Observatory (`/data`)
Source health cards, data availability/coverage heatmap, update times, metadata explorer, failed syncs, freshness and staleness, missing observations, data lineage and downloadable CSV. Users can verify that numbers come from actual sourced records.

### J. Report Builder (`/reports`)
Generate downloadable dated PDF (and optional CSV/JSON) containing country overview, charts, current model estimates if available, forecast periods, methodology, data citations, limitations and as-of dates. Print-friendly report format, not screenshots of a messy page.

## 8. UI and visual design

Design 'premium macro research terminal meets modern fintech': a disciplined, data-dense, polished SaaS aesthetic, not a fake copy of an existing brand. Use dark navy / deep graphite as the default (`#0B1020`, `#131B2C`), crisp neutral text, muted blue/cyan highlights, occasional amber for attention and restrained red for validated negative signals. Minimum WCAG AA contrast where feasible; use color and text/pattern, not color alone, for risk. Think clean side navigation, subtle glass/accent lines, card grids with good whitespace, lovely empty states, smooth but economical animations, responsive desktop/tablet/mobile, beautiful financial typography (Inter + optional IBM Plex Mono for numeric values), clear tabular numbers, hover info, tooltips and chart legends.

UX must be exceptional: skeletons, error/retry states, stale-data banners, downloadable exports, keyboard navigation, logical mobile layout, and no fake controls. Never put a button in the UI unless it has a working behavior. If a feature is planned but unbuilt, clearly disable or omit it, not simulate functionality. Respect reduced-motion preferences. Use consistent component tokens and a design system.

## 9. API design

Implement typed FastAPI endpoints (details may vary):
- `GET /api/health` and `/api/ready`
- `GET /api/countries`
- `GET /api/countries/{iso}/summary?as_of=...`
- `GET /api/indicators?country=...&metric=...&start=...&end=...`
- `GET /api/countries/{iso}/data-quality`
- `GET /api/recession/predict?country=...&horizon=2|4&as_of=...`
- `GET /api/recession/history?country=...&horizon=...`
- `GET /api/forecasts?country=...&metric=...&horizon=...`
- `POST /api/scenarios/evaluate`
- `GET /api/models` and `GET /api/models/{id}/metrics`
- `GET /api/sources/status`
- `POST /api/reports/generate`
- Restricted/safe administrative endpoints for sync/training *only if implemented securely*.

Use consistent structured error contracts, Pydantic schema validation, input bounds, `422` for invalid country/horizon, `503` with actionable error for unavailable model/data, and clear offline-demo metadata. Document with OpenAPI and maintain frontend API typing.

## 10. Security, reliability and operations

- Server-only API keys, no secrets or personally identifying data in logs or fixtures.
- Safe query filtering / SQLAlchemy parameterization; bounded date ranges and payload sizes; reliable external request timeouts; restricted CORS; basic rate limiting for expensive operations.
- No publicly writable 'train model' endpoint, unbounded URL fetch, arbitrary shell execution or unsafe file uploads.
- Input schemas for countries, metrics and scenario values; validate dates and reject unsupported series.
- Structured logging with run IDs, metrics, useful errors and safe user-facing failures.
- SQLite may be used for frictionless demo mode only if PostgreSQL migration compatibility is maintained and documented; production uses PostgreSQL.
- `docker compose up --build`, local dev scripts, migration command, data sync command, ML train command, test command and build command. Supply PowerShell-friendly equivalents or task runner commands.
- Include illustrative `.env.example`, developer docs, architecture diagram, methodology docs, data dictionary, risks/limitations, and clear README screenshot placeholders only until real screenshots are obtained.
- Licensing: respect external data source reuse terms and attribution; avoid committing giant or restricted datasets. Include license and source citations.

## 11. Database and feature pipeline acceptance criteria

- Each KPI card must trace back to a sourced observation with correct transformation and timestamps.
- No false 'Live' badges. Define data freshness as *last successful fetch*, which differs from *observation reference period* and *source publication date*.
- Preprocessing fits only on train split, never across all history.
- Time-based evaluation and future-label censoring are tested.
- Model outputs include a valid prediction timestamp and version, and are reproducible.
- Country-level coverage status reflects the actual data registry.
- PDF/CSV export includes citations, source metadata, units, dates, and important caveats.
- Tests use deterministic tiny local fixtures; live API checks are optional separate integration tests so CI stays stable.
- A one-command demo starts without credentials, with a prominent demo banner. No fake sample values pretending to be current economic data.

## 12. Delivery protocol

First, inspect the repository. Then produce a concise project architecture, data feasibility matrix, phased implementation plan, and explicit acceptance criteria. Begin immediately with Phase 1 unless blocked by an essential missing detail. Do not ask me to pick dozens of libraries. Make defensible choices. After each phase, actually create/edit files, install/check dependencies where available, run lint/tests/build, inspect failures, fix them, and summarize files changed, commands executed, verified outcomes and the single next phase. Never say 'done' for an unimplemented placeholder. Never claim a real-data prediction without verified training.

Build in this order: foundation & design shell -> official-data connectors -> normalized storage/quality -> dashboards -> recession models -> forecasts & explainability -> scenarios & historical replay -> reporting -> deployment, tests & GitHub polish.

**Definition of done:** I can clone the repo; run the documented setup; open a responsive, polished web app; navigate all completed pages; browse real sourced historical macroeconomic data; reproduce at least one genuine training/backtesting pipeline; inspect actual model metrics and a justified probability estimate (or an explicit untrained/unavailable state); verify source provenance; download a report; run tests and a production build. No hidden fake numbers, broken controls, fabricated accuracy or train/test leakage.
