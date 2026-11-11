---
type: codex-run
name: local-deploy-doc
date: 2026-11-11
time: "12:25"
status: failed
exit_code: 1
sandbox: local-single-file
network: false
tags:
  - agent/codex
---

# ❌ Codex · local-deploy-doc

Delegated by Claude Code via `scripts/agents/codex-task.ps1` on 2026-11-11 12:25. Sandbox `local-single-file`, network off, exit code 1.
See [[Agent workflow]] for how delegation and review work.

> [!summary] Codex report
> ```markdown
> # MacroPulse AI — Deployment Guide
>
> This guide covers running the MacroPulse AI stack with Docker Compose. The stack is a local, production-like deployment: PostgreSQL, a FastAPI service, and a Next.js web app. All ports bind to `127.0.0.1` only.
>
> ## What runs
>
> `compose.yml` defines three services:
>
> | Service | Image / build | Port (host) | Notes |
> |---|---|---|---|
> | `db` | `postgres:18-alpine` | `127.0.0.1:5432` | Healthcheck via `pg_isready`. Volume `pgdata` holds the database. |
> | `api` | `apps/api/Dockerfile` | `127.0.0.1:8000` | FastAPI. Healthcheck hits `/api/health`. Volume `models` holds trained artifacts. |
> | `web` | `apps/web/Dockerfile` | `127.0.0.1:3000` | Next.js (standalone). No healthcheck defined in compose. |
>
> - **Volumes**: `pgdata` (PostgreSQL data) and `models` (trained model artifacts).
> - **API healthcheck**: the `api` service is considered healthy when `http://127.0.0.1:8000/api/health` returns HTTP 200.
> - **Web → API proxy**: the Next.js server proxies `/api/*` requests to the API. The target URL (`API_URL`) is baked into the web image at build time (default `http://api:8000`). The browser never sees the API URL; it only talks to the web origin.
>
> ## Configuration
>
> Copy `.env.example` to `.env`. **Never commit `.env`.**
>
> | Variable | Default | Secret? | Purpose |
> |---|---|---|---|
> | `POSTGRES_USER` | `macropulse` | No | PostgreSQL user. |
> | `POSTGRES_PASSWORD` | `change-me-local-only` | **Yes** | PostgreSQL password. |
> | `POSTGRES_DB` | `macropulse` | No | PostgreSQL database name. |
> | `LOG_LEVEL` | `INFO` | No | API log level. |
> | `FRED_API_KEY` | *(empty)* | **Yes** | Optional FRED API key. Leave empty to run without FRED API/ALFRED features. |
> | `API_CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | No | Allowed CORS origins for the API. |
> | `MODELS_DIR` | `/app/models/artifacts` (set in Dockerfile) | No | Directory for trained model artifacts. |
> | `COMPUTE_REQUESTS_PER_MINUTE` | *(unset; in-process limit)* | No | Rate limit for forecast/scenario requests per client address and minute. `0` disables. |
> | `API_URL` | `http://api:8000` (build arg for web) | No | Server-side proxy target. Not exposed to the browser. |
>
> The `DATABASE_URL` for the API is constructed internally from `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` in `compose.yml`.
>
> ## First start
>
> ```powershell
> docker compose up -d --build --wait
> ```
>
> On start, the `api` service runs:
>
> ```sh
> macropulse db upgrade && macropulse serve --host 0.0.0.0 --port 8000
> ```
>
> `macropulse db upgrade` applies database migrations and syncs the registry (idempotent). The API then serves on port 8000.
>
> **Readiness checks:**
>
> ```powershell
> # API readiness
> curl http://127.0.0.1:8000/api/ready
>
> # Web app
> # Open http://localhost:3000 in a browser
> ```
>
> ## Data and models
>
> ### Offline demo snapshot
>
> Load the bundled demo snapshot (genuine official data captured 2026-11-09, no network or keys required):
>
> ```powershell
> docker compose exec api macropulse demo-load
> ```
>
> A **DEMO banner** is shown in the app while snapshot data is in use. The data is not live.
>
> ### Live sync
>
> Replace snapshot data with current data (no keys needed for Eurostat, ECB, and FRED CSV endpoint):
>
> ```powershell
> docker compose exec api macropulse data-sync
> ```
>
> ### Training
>
> Train the model after loading data:
>
> ```powershell
> docker compose exec api macropulse train
> ```
>
> Artifacts persist in the `models` volume.
>
> ### Regular syncs
>
> No scheduler is included. If you need regular data syncs, set up a scheduled job (e.g. cron on Linux/macOS or Windows Task Scheduler) to run `docker compose exec api macropulse data-sync` at your chosen interval.
>
> ## Upgrades
>
> 1. Pull the latest code.
> 2. Rebuild and restart:
>
>    ```powershell
>    docker compose up -d --build --wait
>    ```
>
> 3. Migrations run automatically on API start.
> 4. If model code changed, retrain:
>
>    ```powershell
>    docker compose exec api macropulse train
>    ```
>
> ## Production checklist
>
> - [ ] Set a strong `POSTGRES_PASSWORD` in `.env`.
> - [ ] Terminate TLS at a reverse proxy in front of port 3000 (operator's choice; no proxy is included in this stack).
> - [ ] Set `API_CORS_ORIGINS` to your public origin (e.g. `https://example.com`).
> - [ ] Keep ports bound to `127.0.0.1` or a private network. Do not expose them publicly.
> - [ ] Back up the `pgdata` volume regularly:
>
>   ```powershell
>   docker compose exec db pg_dump -U macropulse macropulse > backup-$(Get-Date -Format yyyyMMdd).sql
>   ```
>
> - [ ] The API rate limit (`COMPUTE_REQUESTS_PER_MINUTE`) is per process. If you run multiple API instances, use a shared limiter (e.g. Redis) to enforce a global limit.
> - [ ] Logs are JSON on stdout. They do not include query strings or secrets.
>
> ## Verification
>
> The CI `docker` job runs the following checks:
>
> ```powershell
> # Build and start the stack
> docker compose up -d --build --wait --wait-timeout 300
>
> # Migrations applied
> docker compose exec -T api macropulse db current
>
> # API readiness
> curl -fsS http://127.0.0.1:8000/api/ready
>
> # Web app responds
> curl -fsS -o /dev/null -w "web %{http_code}\n" http://127.0.0.1:3000/
>
> # Web proxy to API health
> curl -fsS http://127.0.0.1:3000/api/health
>
> # Demo snapshot loaded and served
> docker compose exec -T api macropulse demo-load
> curl -fsS http://127.0.0.1:8000/api/sources/status
> curl -fsS http://127.0.0.1:8000/api/countries/DE/summary
> ```
>
> Additionally, run the smoke test against the API:
>
> ```powershell
> pnpm smoke
> ```
>
> ## Troubleshooting
>
> | Symptom | Action |
> |---|---|
> | API unhealthy | Check logs: `docker compose logs api` |
> | Database not ready | Check DB logs: `docker compose logs db`. Ensure `POSTGRES_PASSWORD` is set. |
> | Port in use | Change the host port in `compose.yml` or stop the conflicting process. |
> | "Model not trained" | Run `docker compose exec api macropulse train` |
> | DEMO banner still shown | Run a live sync: `docker compose exec api macropulse data-sync` |
> ```
>
> - The `API_URL` build arg for the web service is set to `http://api:
> …(truncated)

> [!quote]- Brief sent to Codex
> # Brief
>
> Task: write the deployment guide `docs/DEPLOY.md` for MacroPulse AI.
>
> ## Files
> - CREATE `docs/DEPLOY.md` — the only file you write.
> - CONTEXT (provided below): `compose.yml`, `apps/api/Dockerfile`, `apps/web/Dockerfile`, `.env.example`,
>   `.github/workflows/ci.yml` (the `docker` job shows the exact verified commands), `data/demo/README.md`.
>
> ## Rules
> - Describe ONLY what these files actually do. Do not invent services (no Kubernetes, no Nginx config,
>   no TLS certificates, no cloud provider steps) and do not claim anything was tested beyond what the CI
>   `docker` job runs. Where the operator must decide something (TLS, backups, secrets store), say so
>   plainly as a checklist item, without inventing tooling.
> - Commands in fenced blocks, PowerShell-friendly where they differ (Windows is the main dev platform;
>   docker commands are the same on both).
> - British/neutral English, concise, headings `##` / `###`, tables where useful.
>
> ## Required sections
> 1. **What runs** — the three compose services (db PostgreSQL 18, api FastAPI on 8000, web Next.js on 3000),
>    ports bound to 127.0.0.1 only, volumes `pgdata` and `models`, the api healthcheck, the web → api
>    server-side proxy (`API_URL` baked at build time; the browser never sees the API URL).
> 2. **Configuration** — every variable from `.env.example` relevant to compose, with its default and
>    whether it is a secret (`POSTGRES_PASSWORD`, `FRED_API_KEY`). Say that `.env` is never committed.
> 3. **First start** — `docker compose up -d --build --wait`, then what happens automatically (migrations
>    and registry sync on api start: see the api `CMD`), then readiness checks
>    (`curl http://127.0.0.1:8000/api/ready`, open http://localhost:3000).
> 4. **Data and models** — either the offline demo snapshot
>    (`docker compose exec api macropulse demo-load`, banner shown, not live) or a live sync
>    (`docker compose exec api macropulse data-sync`), then training
>    (`docker compose exec api macropulse train`; artifacts persist in the `models` volume). Mention a
>    scheduled job (e.g. cron / Windows Task Scheduler) is the operator's choice for regular syncs; no
>    scheduler is included.
> 5. **Upgrades** — pull, `docker compose up -d --build --wait`; migrations run on start; retrain after a
>    model-code change.
> 6. **Production checklist** — strong `POSTGRES_PASSWORD`; TLS terminated by a reverse proxy in front of
>    port 3000 (operator's choice); set `API_CORS_ORIGINS` to the public origin; keep ports on localhost
>    or a private network; backups of `pgdata` (`docker compose exec db pg_dump ...`); the API rate limit
>    (`COMPUTE_REQUESTS_PER_MINUTE`) is per process — use a shared limiter for several API instances;
>    logs are JSON on stdout without query strings or secrets.
> 7. **Verification** — the exact checks the CI `docker` job runs, and `pnpm smoke` against the API.
> 8. **Troubleshooting** — api unhealthy (logs: `docker compose logs api`), database not ready, port in use,
>    "Model not trained" (run train), demo banner still shown (run a live sync).
>
> # Output file
>
> `docs/DEPLOY.md`
>
> # Context files
>
> ## `compose.yml`
>
> ```yml
> # MacroPulse AI — local production-like stack: PostgreSQL + FastAPI + Next.js.
> #   docker compose up --build        then open http://localhost:3000
> # Values come from `.env` (see .env.example); ports bind to localhost only.
> name: macropulse
>
> services:
>   db:
>     image: postgres:18-alpine
>     environment:
>       POSTGRES_USER: ${POSTGRES_USER:-macropulse}
>       POSTGRES_PASSWORD:***
>       POSTGRES_DB: ${POSTGRES_DB:-macropulse}
>     volumes:
>       - pgdata:/var/lib/postgresql
>     ports:
>       - "127.0.0.1:5432:5432"
>     healthcheck:
>       test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
>       interval: 5s
>       timeout: 3s
>       retries: 10
>
>   api:
>     build:
>       context: .
>       dockerfile: apps/api/Dockerfile
>     environment:
>       APP_ENV: production
>       LOG_LEVEL: ${LOG_LEVEL:-INFO}
>       DATABASE_URL: postgresql+psycopg://${POSTGRES_USER:-macropulse}:${POSTGRES_PASSWORD:***
>       API_CORS_ORIGINS: http://localhost:3000,http://127.0.0.1:3000
>       FRED_API_KEY:***
>       MODELS_DIR: /app/models/artifacts
>     volumes:
>       - models:/app/models/artifacts
>     depends_on:
>       db:
>         condition: service_healthy
>     ports:
>       - "127.0.0.1:8000:8000"
>
>   web:
>     build:
>       context: .
>       dockerfile: apps/web/Dockerfile
>       args:
>         API_URL: http://api:8000
>     depends_on:
>       api:
>         condition: service_healthy
>     ports:
>       - "127.0.0.1:3000:3000"
>
> volumes:
>   pgdata: {}
>   models: {}
>
> ```
>
> ## `apps/api/Dockerfile`
>
> ```text
> # syntax=docker/dockerfile:1.7
> # Build context: repository root (uv workspace). `docker compose build api`
> FROM python:3.12-slim AS runtime
>
> ENV PYTHONDONTWRITEBYTECODE=1 \
>     PYTHONUNBUFFERED=1 \
>     UV_COMPILE_BYTECODE=1 \
>     UV_LINK_MODE=copy \
>     UV_PYTHON_DOWNLOADS=never
>
> COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/
>
> WORKDIR /app
>
> # 1) third-party dependencies only (cached layer)
> COPY pyproject.toml uv.lock .python-version ./
> COPY apps/api/pyproject.toml apps/api/pyproject.toml
> COPY packages/economics/pyproject.toml packages/economics/pyproject.toml
> COPY packages/ml/pyproject.toml packages/ml/pyproject.toml
> RUN --mount=type=cache,target=/root/.cache/uv \
>     uv sync --frozen --no-dev --all-packages --no-install-workspace
>
> # 2) workspace sources
> COPY apps/api apps/api
> COPY packages/economics packages/economics
> COPY packages/ml packages/ml
> # Genuine demo snapshot (108 KB) for `macropulse demo-load` without network or keys.
> COPY data/demo data/demo
> RUN --mount=type=cache,target=/root/.cache/uv \
>     uv sync --frozen --no-dev --all-packages
>
> RUN useradd --create-home --uid 10001 app \
>     && mkdir -p /app/data /app/models/artifacts \
>     && chown -R app /app/data /app/models
> USER app
> # Trained artifacts live on a volume (compose: `models`); train with `docker compose exec api macropulse train`.
> ENV PATH="/app/.venv/bin:${PATH}" \
>     MODEL
> …(truncated)
