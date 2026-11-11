# MacroPulse AI — Deployment Guide

> Drafted by the local model (Qwen3.8-27B) from `compose.yml`, the Dockerfiles, `.env.example` and the CI `docker` job, then reviewed and corrected by the lead (CORS/rate-limit settings now read from `.env`, a binary-safe backup, `curl.exe` in PowerShell).

This guide covers running the MacroPulse AI stack with Docker Compose. The stack is a local, production-like deployment: PostgreSQL, a FastAPI service, and a Next.js web app. All ports bind to `127.0.0.1` only.

## What runs

`compose.yml` defines three services:

| Service | Image / build | Port (host) | Notes |
|---|---|---|---|
| `db` | `postgres:18-alpine` | `127.0.0.1:5432` | Healthcheck via `pg_isready`. Volume `pgdata` holds the database. |
| `api` | `apps/api/Dockerfile` | `127.0.0.1:8000` | FastAPI. Healthcheck hits `/api/health`. Volume `models` holds trained artifacts. |
| `web` | `apps/web/Dockerfile` | `127.0.0.1:3000` | Next.js (standalone). No healthcheck defined in compose. |

- **Volumes**: `pgdata` (PostgreSQL data) and `models` (trained model artifacts).
- **API healthcheck**: the `api` service is considered healthy when `http://127.0.0.1:8000/api/health` returns HTTP 200.
- **Web → API proxy**: the Next.js server proxies `/api/*` requests to the API. The target URL (`API_URL`) is baked into the web image at build time (default `http://api:8000`). The browser never sees the API URL; it only talks to the web origin.

## Configuration

Copy `.env.example` to `.env`. **Never commit `.env`.**

| Variable | Default | Secret? | Purpose |
|---|---|---|---|
| `POSTGRES_USER` | `macropulse` | No | PostgreSQL user. |
| `POSTGRES_PASSWORD` | `change-me-local-only` | **Yes** | PostgreSQL password. |
| `POSTGRES_DB` | `macropulse` | No | PostgreSQL database name. |
| `LOG_LEVEL` | `INFO` | No | API log level. |
| `FRED_API_KEY` | *(empty)* | **Yes** | Optional FRED API key. Leave empty to run without FRED API/ALFRED features. |
| `API_CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | No | Allowed CORS origins for the API (comma-separated; a wildcard is refused). |
| `MODELS_DIR` | `/app/models/artifacts` (set in Dockerfile) | No | Directory for trained model artifacts. |
| `COMPUTE_REQUESTS_PER_MINUTE` | `240` | No | Forecast, scenario and report requests per client address and minute (in-process). `0` disables. |
| `API_URL` | `http://api:8000` (build arg for web) | No | Server-side proxy target. Not exposed to the browser. |

The `DATABASE_URL` for the API is constructed internally from `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` in `compose.yml`.

## First start

```powershell
docker compose up -d --build --wait
```

On start, the `api` service runs:

```sh
macropulse db upgrade && macropulse serve --host 0.0.0.0 --port 8000
```

`macropulse db upgrade` applies database migrations and syncs the registry (idempotent). The API then serves on port 8000.

**Readiness checks:**

```powershell
# API readiness (PowerShell: use curl.exe, plain `curl` is an alias of Invoke-WebRequest)
curl.exe http://127.0.0.1:8000/api/ready
# then open http://localhost:3000 in a browser
```

## Data and models

### Offline demo snapshot

Load the bundled demo snapshot (genuine official data captured 2026-11-09, no network or keys required):

```powershell
docker compose exec api macropulse demo-load
```

A **DEMO banner** is shown in the app while snapshot data is in use. The data is not live.

### Live sync

Replace snapshot data with current data (no keys needed for Eurostat, ECB, and FRED CSV endpoint):

```powershell
docker compose exec api macropulse data-sync
```

### Training

Train the model after loading data:

```powershell
docker compose exec api macropulse train
```

Artifacts persist in the `models` volume.

### Regular syncs

No scheduler is included. If you need regular data syncs, set up a scheduled job (e.g. cron on Linux/macOS or Windows Task Scheduler) to run `docker compose exec api macropulse data-sync` at your chosen interval.

## Upgrades

1. Pull the latest code.
2. Rebuild and restart:

   ```powershell
   docker compose up -d --build --wait
   ```

3. Migrations run automatically on API start.
4. If model code changed, retrain:

   ```powershell
   docker compose exec api macropulse train
   ```

## Production checklist

- [ ] Set a strong `POSTGRES_PASSWORD` in `.env`.
- [ ] Terminate TLS at a reverse proxy in front of port 3000 (operator's choice; no proxy is included in this stack).
- [ ] Set `API_CORS_ORIGINS` to your public origin (e.g. `https://example.com`).
- [ ] Keep ports bound to `127.0.0.1` or a private network. Do not expose them publicly.
- [ ] Back up the database regularly. Dump inside the container and copy the file out (binary-safe on
  Windows PowerShell, where redirecting `>` would re-encode the dump):

  ```powershell
  docker compose exec -T db pg_dump -U macropulse -Fc -f /tmp/macropulse.dump macropulse
  docker compose cp db:/tmp/macropulse.dump ./macropulse.dump
  # restore: docker compose cp ./macropulse.dump db:/tmp/ ; docker compose exec -T db pg_restore -U macropulse -d macropulse --clean /tmp/macropulse.dump
  ```

- [ ] The API rate limit (`COMPUTE_REQUESTS_PER_MINUTE`) is per process. If you run multiple API instances, use a shared limiter (e.g. Redis) to enforce a global limit.
- [ ] Logs are JSON on stdout. They do not include query strings or secrets.

## Verification

The CI `docker` job runs the following checks (bash on `ubuntu-latest`; in PowerShell use `curl.exe`):

```bash
# Build and start the stack
docker compose up -d --build --wait --wait-timeout 300

# Migrations applied
docker compose exec -T api macropulse db current

# API readiness
curl -fsS http://127.0.0.1:8000/api/ready

# Web app responds
curl -fsS -o /dev/null -w "web %{http_code}\n" http://127.0.0.1:3000/

# Web proxy to API health
curl -fsS http://127.0.0.1:3000/api/health

# Demo snapshot loaded and served
docker compose exec -T api macropulse demo-load
curl -fsS http://127.0.0.1:8000/api/sources/status
curl -fsS http://127.0.0.1:8000/api/countries/DE/summary
```

Additionally, from a checkout with uv installed, run the end-to-end API checks against the stack:

```powershell
uv run python scripts/smoke_api.py --base-url http://127.0.0.1:8000
```

## Troubleshooting

| Symptom | Action |
|---|---|
| API unhealthy | Check logs: `docker compose logs api` |
| Database not ready | Check DB logs: `docker compose logs db`. Ensure `POSTGRES_PASSWORD` is set. |
| Port in use | Change the host port in `compose.yml` or stop the conflicting process. |
| "Model not trained" | Run `docker compose exec api macropulse train` |
| DEMO banner still shown | Run a live sync: `docker compose exec api macropulse data-sync` |
