# MacroPulse AI

**Macroeconomic intelligence and technical-recession early warning, built only on official statistics.**

MacroPulse AI monitors Belgium, Germany, France, the Netherlands and the United States using data from
Eurostat, the ECB, FRED, the World Bank and the OECD, and (from Phase 5) estimates the probability of a
*technical recession* — at least two consecutive quarters of negative real-GDP q/q growth — within the
next 2 or 4 quarters, with transparent, walk-forward-evaluated and calibrated models.

> **Engineering truth over flashy claims.** The UI never shows a number that is not traced to a sourced
> observation or a measured model output. Unbuilt modules say so. Missing data stays missing.

![MacroPulse overview — real screenshot of the Phase 4 production build with stored official data](docs/screenshots/overview.png)

| Recession risk (DE, 4 quarters) | ML laboratory | Country explorer (US, NBER reference bands) |
| --- | --- | --- |
| ![Recession risk](docs/screenshots/recession.png) | ![ML laboratory](docs/screenshots/lab.png) | ![Country explorer](docs/screenshots/country-de.png) |

| Compare (HICP vs CPI) | Data observatory |
| --- | --- |
| ![Compare](docs/screenshots/compare.png) | ![Data observatory](docs/screenshots/data-observatory.png) |

## Status

The project is built in ten verified phases ([roadmap](docs/ROADMAP.md)). **Phases 1–8 are complete:**
foundation, production-grade UI system, official-data ingestion, dashboards on the stored data, the
technical-recession target with a first evaluated model, the explainable risk dashboard with the ML
laboratory, the forecast studio with the scenario lab, and the crisis time machine. Phase 9 (PDF reports)
is next.

> [!IMPORTANT]
> **Model result, stated plainly.** The published models beat the historical base rate on the 2000–2014
> development backtest (Brier skill +0.10 for 2 quarters ahead, +0.03 for 4) but **not on the held-out
> years 2015–2026** (−0.45 and −0.75). COVID-2020 cannot be foreseen from these macro inputs, and the
> 2022–24 yield-curve inversion produced false alarms. Probabilities are therefore shown as analytical
> estimates with this track record — never as forecasts of certainty.

| Area | Working now (verified) | Next |
| --- | --- | --- |
| Monorepo | pnpm + uv workspaces, pinned deps, lockfiles, `.env.example`, CI, Dockerfiles, compose | — |
| Official data | `macropulse data-sync`: Eurostat (JSON-stat), ECB (SDMX CSV) and FRED connectors with timeouts, retries/backoff, `Retry-After`, throttling, response validation, idempotent upserts, per-series quality checks and partial-failure runs. **Live run 2026-11-09: 25,702 observations from 31 series** (incl. 10-year yields and 3-month rates), all runs succeeded | OECD and World Bank connectors; FRED API-key metadata/ALFRED vintages |
| API (FastAPI) | `/api/health`, `/api/ready`, `/api/countries` (support levels computed from stored data: BE/DE/FR/NL `full`, US `partial`), `/api/sources/status`, `/api/indicators/catalog`, `/api/indicators?country=&indicator=&start=&end=` (derived series + provenance + quality checks), **`/api/countries/{iso2}/summary?as_of=`** (KPI values, change, staleness, provenance), **`/api/countries/{iso2}/data-quality`**, **`/api/data-quality`**, **`/api/observations/export`** (raw CSV), **`/api/recession/predict`** (live inference from the saved artifact, explanation, track record, in-sample flag), **`/api/recession/history`** (walk-forward estimates + realised recessions), **`/api/models`**, **`/api/models/{id}/metrics`**, **`/api/models/{id}/curves`** (read-only; training is a CLI operation), **`/api/forecasts`** (paths, empirical intervals, rolling-origin backtest metrics and errors), **`/api/scenarios/spec`** and **`POST /api/scenarios/evaluate`** (bounded shocks, baseline vs scenario, contribution deltas, out-of-distribution checks; rate-limited), **`/api/history/replay`**, **`/api/history/episodes`** and **`/api/history/presets`** (walk-forward replay with inputs as known then, outcome as published later, warned/missed/false alarms); structured error contract, request ids, JSON logs, restricted CORS; Alembic migrations (SQLite ↔ PostgreSQL) | Report generation (Phase 9) |
| Web (Next.js 16) | **Overview, Country Explorer, Compare and Data Observatory on stored official data:** KPI tiles with value, change, source flag and provenance tooltip; ECharts with hover source, history window, as-of cut-off, NBER reference bands (US, labelled as external), step lines for rate decisions, table view, CSV (with citations) and PNG export; compare up to four countries as published or as spread vs a baseline, with comparability warnings; per-series lineage with quality checks and raw-row CSV. **Recession risk:** probability gauge with bands and base rate, model version / as-of / freshness, contributions, walk-forward risk timeline with realised recessions, track record and limitations. **ML laboratory:** model comparison, calibration, ROC/PR, confusion matrix, per-country metrics, fold timeline, coefficients, reproducibility card. **Forecast studio:** naive, rolling-mean and ridge-AR forecasts with dashed projection and an empirical 80 % ribbon, later-published values for a past as-of, backtest table (MAE, RMSE vs naive, measured coverage with under-coverage flagged), backtest chart, assumptions, CSV/PNG. **Scenario lab:** bounded sliders, baseline vs scenario probability, contribution deltas, training-range and joint plausibility warnings, non-causal disclaimer, reset, shareable URL, save in the browser, JSON export. **Crisis time machine:** crisis presets and a quarter scrubber, the walk-forward estimate with its fold and verdict, inputs as known at the cut-off with lags, outcome window, NBER months as a separate US reference, warnings/misses/false alarms with one-click replay, labelled a revised-data / release-lag approximation. URL-shareable context; loading / error-with-retry / not-synced / not-trained states; no overflow at 375 px | Report builder (Phase 9) |
| Data feasibility | 45 live probes of official endpoints → [`docs/DATA_FEASIBILITY.md`](docs/DATA_FEASIBILITY.md); HICP successor `prc_hicp_minr` verified | — |
| Models | `macropulse train`: technical-recession labels (H = 2, 4) with censoring, as-of feature snapshots with conservative publication lags (GDP, inflation, unemployment, policy rate, term spread), yearly walk-forward backtest with horizon purge, prevalence and contraction-rule baselines, Logistic Regression, HistGradientBoosting (± temporal Platt calibration); per-split and per-country metrics, OOS predictions and versioned artifacts. Selection uses development data only and requires beating the baseline | Better leading indicators, vintages (later phases) |

Verified on 2026-11-10 (Windows 11): 234 pytest tests (+1 PostgreSQL test that runs in CI, +16 opt-in live
API tests run with `MACROPULSE_LIVE_TESTS=1`), ruff, mypy `--strict`; ESLint, `tsc`, 97 Vitest tests and
`next build`; a live `data-sync` against Eurostat, ECB and FRED (25,702 observations); a real training run;
`pnpm smoke` — 2818/2818 end-to-end API checks including the inference round trip for 5 countries × 2 horizons,
all 15 forecast series, the scenario round trip and 40 crisis replays; browser checks of the data pages (1440 px and 375 px), the
Recession risk and ML laboratory pages, the Forecast studio and Scenario lab (save/load/reset included) and the
Crisis time machine (presets, scrubber, episode links).
**Not automated yet:** browser-level end-to-end tests (the page checks above were done by hand).
**Not verified locally:** `docker compose up` (Docker is not installed on the development machine — CI builds
the images).

## Quickstart

Prerequisites: **Node.js ≥ 22.12** with **pnpm** (`npm i -g pnpm`), **Python 3.12** with
**[uv](https://docs.astral.sh/uv/)**. Docker is optional.

```powershell
# Windows PowerShell (same commands on macOS/Linux)
pnpm bootstrap    # pnpm install + uv sync + migrate the local SQLite database
pnpm data:sync    # fetch the official series (Eurostat, ECB, FRED) — needs internet, ~15 s
pnpm dev          # API on http://127.0.0.1:8000, web on http://localhost:3000
```

- App: <http://localhost:3000> · API docs (OpenAPI): <http://127.0.0.1:8000/api/docs>
- Local development uses SQLite (`data/local/macropulse.db`); production uses PostgreSQL.
- Optional: copy `.env.example` to `.env` and set `FRED_API_KEY` (server-side only) for FRED/ALFRED features.

With Docker (PostgreSQL + API + web):

```bash
docker compose up --build
# then, inside the API container (data and models persist in volumes):
docker compose exec api macropulse data-sync
docker compose exec api macropulse train
```

### Commands

| Command | What it does |
| --- | --- |
| `pnpm dev` / `pnpm dev:api` / `pnpm dev:web` | Run both services / API only / web only |
| `pnpm db:upgrade` | Apply migrations and sync the country/source registry (idempotent) |
| `pnpm data:sync` | Fetch all mapped official series. Narrow it with `uv run macropulse data-sync --source eurostat --country DE`. Exit code 1 if any run is partial or failed |
| `$env:MACROPULSE_LIVE_TESTS = "1"; uv run pytest -m live` | Opt-in checks against the real APIs (not run in CI) |
| `pnpm smoke` | End-to-end checks of a running API over the stored data (provenance, support levels, CSV row counts, error contract, inference, forecasts, scenarios, replays) |
| `pnpm train` | Build as-of features from the stored data, run the walk-forward backtest for H = 2 and 4, store metrics/predictions and save the published model to `models/artifacts/` (`--horizon`, `--seed`, `--no-artifacts`) |
| `pnpm test` | pytest + Vitest |
| `pnpm lint` | ruff, ruff format, mypy, ESLint, tsc |
| `pnpm build` | Next.js production build |
| `pnpm gen:types` | Regenerate TypeScript API types from the FastAPI OpenAPI schema |
| `uv run python scripts/probe_sources.py --out docs/data-feasibility-probe.json` | Re-run the live source feasibility probe |

## Architecture

```mermaid
flowchart LR
  B[Browser] -->|same-origin /api/*| W[Next.js 16 App Router<br/>TanStack Query · typed client]
  W -->|server-side rewrite| A[FastAPI · Pydantic v2]
  A --> D[(PostgreSQL / SQLite<br/>SQLAlchemy 2 · Alembic)]
  S[Eurostat · ECB · FRED] -->|data-sync CLI| D
  S2[World Bank · OECD] -.->|connectors planned| D
  M[ML pipeline · Phase 5] -.-> D
```

- **One typed contract:** Pydantic models → OpenAPI → `packages/shared-types` (openapi-typescript) →
  `openapi-fetch` in the browser. CI fails if the committed schema or types drift.
- **Honest state everywhere:** country support levels are *computed* from stored observations; source
  freshness is the *last successful fetch*, derived from recorded ingestion runs. Derived indicators (q/q, y/y)
  are computed at read time from the native series and only across adjacent published periods — gaps stay gaps.
- Details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Methodology (summary)

- **Target:** a technical recession occurs within horizon H ∈ {2, 4} if at least one pair of consecutive
  quarters with negative q/q real-GDP growth lies entirely inside the next H quarters. Zero growth is not
  negative; labels whose horizon is not yet observable are censored.
- **NBER is not the target.** US NBER recession dates (FRED `USREC`) are shown only as an external reference.
- **No leakage:** walk-forward evaluation with horizon gaps; scalers/imputers fit on training folds only;
  as-of feature snapshots with conservative release lags. Without true vintages (Eurostat), historical
  replays are labelled *revised-data / release-lag approximation*.
- **Metrics that matter for rare events:** Brier score, log loss, calibration, PR-AUC and baselines — not
  accuracy on mostly non-recession quarters.
- **Protocol as implemented:** yearly expanding-window folds from 2000; development years 2000–2014,
  held-out 2015 onwards; the published model is the development-best candidate only if it beats the
  prevalence baseline there, otherwise the baseline itself is published. Details:
  `vault/50 Methodology/Evaluation protocol.md`.

## Data sources and attribution

| Source | Used for | Terms |
| --- | --- | --- |
| [Eurostat](https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-introduction) | Quarterly real GDP (`namq_10_gdp`), unemployment, HICP, government debt | Reuse with acknowledgement |
| [ECB Data Portal](https://data.ecb.europa.eu/help/api/overview) | Shared euro area policy rates | Reuse with source attribution |
| [FRED / ALFRED](https://fred.stlouisfed.org/docs/api/fred/series_observations.html) | US indicators, vintages, NBER reference | Series-specific; see FRED legal |
| [World Bank](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392) | Annual structural indicators | CC BY 4.0 |
| [OECD](https://data-explorer.oecd.org/) | Composite leading indicators | OECD terms |

NBER business-cycle dating reference:
<https://www.nber.org/research/business-cycle-dating/business-cycle-dating-procedure-frequently-asked-questions>.
Key feasibility findings (e.g. Eurostat's `prc_hicp_manr` ends at 2025-12; OECD CLI is not published for
BE/NL) are in [`docs/DATA_FEASIBILITY.md`](docs/DATA_FEASIBILITY.md).

## Repository layout

```
apps/web               Next.js App Router frontend (TypeScript strict, Tailwind v4, TanStack Query)
apps/api               FastAPI service, Alembic migrations, CLI (`macropulse`)
packages/economics     Country/indicator registry, official-data connectors, transforms, quality rules
packages/shared-types  Generated TypeScript types from the OpenAPI schema
scripts/               Source probe; scripts/agents for AI-agent delegation
docs/                  Architecture, roadmap, data feasibility (+ raw probe evidence)
```

## Knowledge base (Obsidian)

`vault/` is an [Obsidian](https://obsidian.md) vault holding the project's memory: live status, phase notes,
architecture decisions (ADRs), verified data sources and findings, methodology, Codex run reports, daily
session journals, Bases dashboards and an architecture canvas. Claude Code hooks (`.claude/settings.json`)
and the Codex runner log activity automatically into `vault/80 Logs/` (local only, secrets redacted). Open the
`vault` folder in Obsidian and start at **Home**.

## AI-assisted development

Built with Claude Code as lead engineer and OpenAI Codex for scoped side tasks (briefs in `.agents/briefs/`,
rules in [`AGENTS.md`](AGENTS.md), runner `scripts/agents/codex-task.ps1`). Every delegated result is reviewed
and re-verified before it is accepted; nothing is reported as working without being run.

## Disclaimer

MacroPulse AI produces analytical estimates for research and education. It is not investment advice, and
model probabilities are not certainties.

## License

Code: [MIT](LICENSE). Data remains subject to each publisher's terms (see above).
