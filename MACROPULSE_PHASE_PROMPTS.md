# MacroPulse AI — Implementation Phase Prompts

## Prompt 1 — Product blueprint and repository setup

Read the MASTER PROMPT. Audit the current repository, then implement the monorepo foundation end-to-end: Next.js frontend, FastAPI backend, design tokens, nav, functional routing, PostgreSQL compose file, env example, typed health endpoint and smoke tests. Produce a concise architecture/data feasibility matrix and agree internally on the initial five countries. Include one `make dev` or documented equivalent workflow. Run install/build/lint/tests and fix errors. Do not build disconnected cosmetic mock dashboards.

## Prompt 2 — Production-grade UI system

Create a refined, responsive MacroPulse AI design system. Implement sidebar, topbar, country selector, as-of selector, chart wrappers, KPI cards, missing-data and stale-data states, loading skeletons, error boundaries, tooltips and mobile menus. Implement all page layouts with strictly empty/unavailable states wired to typed API queries rather than fake numbers. Ensure navigation, selectors, buttons and filters all work. Take screenshots if environment supports it; inspect and fix overflow and broken interactions. Run frontend build and tests.

## Prompt 3 — Economic data ingestion and metadata

Implement and VERIFY at least two live official adapters, beginning with Eurostat quarterly `namq_10_gdp` and one other feasible Eurostat indicator, with ECB and FRED added as practical. Discover correct dimensions from official metadata instead of guessing. Store observations with unit, frequency, country, seasonal adjustment, observation period, retrieval and publication/vintage dates if known, and source URL. Add retries, source registry, transform tests, partial-failure handling, local deterministic test fixtures, CLI `data-sync` and source-health API. Show real returned row counts and failures. Never fabricate missing data.

## Prompt 4 — Data coverage and actual dashboards

Wire Overview, Country Explorer, Compare and Data Observatory to actual API endpoints. Show provenance on each KPI and hover chart. Implement country selection, time range, unit/frequency labels, comparative alignment, source-health and coverage matrix, CSV export, chart empty states and data freshness. Validate Belgium, Germany, France, Netherlands and US as supported/partial/unavailable based on actual source coverage. Make these four pages truly usable before proceeding. Run end-to-end smoke tests and build.

## Prompt 5 — Recession target, time-aware features and first real model

Implement a documented binary target: whether there are two consecutive negative q/q real GDP quarters entirely within the next H=2 or H=4 future quarters. Validate zero/missing handling and temporal alignment. Create as-of quarterly features, conservative feature publication lags and explicit vintage availability flags. Build prevalence baseline, Logistic Regression and XGBoost challenger if available. Use expanding-window backtesting with a horizon gap; fit transforms on train only. Compute Brier, log loss, ROC/PR AUC when defined, calibration and precision/recall. Save model versions with data cutoff and metadata. Include leakage unit tests and real sample/event counts. No fabricated model metrics.

## Prompt 6 — Explainable risk dashboard and model laboratory

Connect the actual saved and evaluated models to `/recession` and `/lab`. Add 2Q/4Q horizon switch, model version, as-of date, calibrated probability, honest risk categories, feature contribution charts with SHAP or documented fallback, split timeline, calibration plot, ROC/PR curves where valid, baseline comparison and sample sizes. Add actionable unavailable states when models/metrics are missing. Validate an actual inference round-trip from real stored data to UI. Avoid pseudo-predictions. Add tests for unsupported countries/horizons.

## Prompt 7 — Forecasts and scenario simulator

Build forecasts for GDP growth, inflation and unemployment starting with naive baselines and one stronger reproducible model, with rolling evaluation and empirically justified intervals. Then implement Scenario Lab with slider-driven baseline vs altered inputs, model sensitivity delta, unsupported/out-of-distribution flag, explicit non-causal warning, reset/save/export actions. Debounce API requests and limit values. Require all controls to visibly alter real calculations, not decorative graphs. Run tests and demonstrate one complete user interaction.

## Prompt 8 — Historical Crisis Time Machine

Implement historic as-of replay with strict temporal eligibility. For US, support ALFRED vintages when verified and available; for European sources where revisions lack archival vintages, show a conspicuous 'revised-data / release-lag approximation' label. Add time scrubber, known-at-date features panel, predicted risk vs subsequently observed outcome, recession-event markers and false-positive/false-negative examples. Protect against training a replay model on future outcomes. Document exact limitations and run temporal-leakage tests.

## Prompt 9 — Analyst-grade PDF reports

Implement a polished PDF report for selected country, as-of date, macro indicators, comparative charts, model predictions when available, forecast methodology, risk drivers, source citations, data freshness and uncertainty limitations. Offer valid file download with a descriptive name and server-side errors. Include a plain-language executive summary generated from rules/metrics (no invented LLM analysis). Verify resulting PDF opens, includes accurate tables/charts, handles missing data and doesn't expose credentials. Also enable CSV export for chart data.

## Prompt 10 — Production hardening, audit and GitHub-ready release

Perform a full code and design audit. Fix TypeScript, Python lint and type issues, broken routes, stale-data errors, responsive layout bugs and inaccessible controls. Run realistic smoke/E2E tests across core pages, a backend test suite, frontend build and docker-compose setup. Check security basics (secrets, CORS, input validation, unsafe jobs, dependencies). Write excellent README with architecture, quickstart for Windows, real sample screenshots only if generated, data-source attribution, ML target definition, rigorous methodology, model scores only if measured, limitations, roadmap and resume bullets. Produce a truthful final table: working, partly working, not implemented. Never declare the build complete if major checks fail.

---

# BONUS PROMPTS

## A. Design critique

Act as a senior fintech product designer and QA reviewer. Inspect every MacroPulse page on desktop and mobile. Identify the top 20 usability, information hierarchy, typography, interaction, contrast and visualization flaws. Then fix them directly in code. Do not replace working data integration with static screenshots. Provide before/after evidence where possible and run builds.

## B. Economic methodology audit

Act as a skeptical economic researcher auditing recession ML. Review labeling, target event dates, point-in-time availability, data revisions, sample size, class imbalance, cross-country pooling, calibration, drift and false positives. Find any hidden leakage, non-comparable units, overconfident claims or misleading charts. Fix the pipeline and tests, and update `/lab` methodology explanations. Do not just write a report; implement corrections.

## C. Security audit

Act as an application security engineer. Audit secrets, inbound validation, SQL safety, egress endpoints, CORS, CORS credentials, rates and expensive task endpoints, exports, upload handling and log contents. Fix concrete issues and add test coverage. Do not introduce authentication complexity unless clearly justified by the actual functionality.

## D. Final recruiter demo

Prepare a concise 3-minute recruiter demo for a financial analyst / consulting interview. Pick a country with full data, show an authentic macro trend, explain recession target and model drivers, demonstrate validation/calibration, run a what-if analysis with the non-causal caveat, and export a source-cited report. Also create truthful resume bullets naming actual tools and measurable outcomes only if verified. Add a `docs/DEMO_SCRIPT.md` file.

---

# CHECKLIST — Actual completion only

- [ ] `docker compose up --build` starts services (or documented verified equivalent).
- [ ] No secret keys in client bundle or Git history.
- [ ] Frontend uses actual typed backend API.
- [ ] Country and as-of selections change data on-screen.
- [ ] Source links, retrieval dates, release-period notes appear.
- [ ] Unavailable features display honest messages.
- [ ] Real recession target and label censoring implemented.
- [ ] Walk-forward evaluation with horizon-safe gaps passes tests.
- [ ] Brier/calibration and baseline comparisons shown.
- [ ] Scenario dashboard labeled non-causal.
- [ ] Historical replay vintage limitations clearly communicated.
- [ ] Responsive UI and keyboard controls tested.
- [ ] Working PDF report with citations and uncertainty notes.
- [ ] README setup, methodology, data limitations, commands and screenshots accurate.
- [ ] No invented economic stats, no fake model metrics, no inaccessible dead-end buttons.

## Development note

A truly impressive MacroPulse repository demonstrates analytical judgment, not just a slick dashboard. Reproducible modeling, honest timestamps, valid temporal evaluation, proper uncertainty and traceable economic data will stand out far more in investment/consulting interviews than a large decorative neural network that cannot defend its results.
