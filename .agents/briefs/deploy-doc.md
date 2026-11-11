Task: write the deployment guide `docs/DEPLOY.md` for MacroPulse AI.

## Files
- CREATE `docs/DEPLOY.md` — the only file you write.
- CONTEXT (provided below): `compose.yml`, `apps/api/Dockerfile`, `apps/web/Dockerfile`, `.env.example`,
  `.github/workflows/ci.yml` (the `docker` job shows the exact verified commands), `data/demo/README.md`.

## Rules
- Describe ONLY what these files actually do. Do not invent services (no Kubernetes, no Nginx config,
  no TLS certificates, no cloud provider steps) and do not claim anything was tested beyond what the CI
  `docker` job runs. Where the operator must decide something (TLS, backups, secrets store), say so
  plainly as a checklist item, without inventing tooling.
- Commands in fenced blocks, PowerShell-friendly where they differ (Windows is the main dev platform;
  docker commands are the same on both).
- British/neutral English, concise, headings `##` / `###`, tables where useful.

## Required sections
1. **What runs** — the three compose services (db PostgreSQL 18, api FastAPI on 8000, web Next.js on 3000),
   ports bound to 127.0.0.1 only, volumes `pgdata` and `models`, the api healthcheck, the web → api
   server-side proxy (`API_URL` baked at build time; the browser never sees the API URL).
2. **Configuration** — every variable from `.env.example` relevant to compose, with its default and
   whether it is a secret (`POSTGRES_PASSWORD`, `FRED_API_KEY`). Say that `.env` is never committed.
3. **First start** — `docker compose up -d --build --wait`, then what happens automatically (migrations
   and registry sync on api start: see the api `CMD`), then readiness checks
   (`curl http://127.0.0.1:8000/api/ready`, open http://localhost:3000).
4. **Data and models** — either the offline demo snapshot
   (`docker compose exec api macropulse demo-load`, banner shown, not live) or a live sync
   (`docker compose exec api macropulse data-sync`), then training
   (`docker compose exec api macropulse train`; artifacts persist in the `models` volume). Mention a
   scheduled job (e.g. cron / Windows Task Scheduler) is the operator's choice for regular syncs; no
   scheduler is included.
5. **Upgrades** — pull, `docker compose up -d --build --wait`; migrations run on start; retrain after a
   model-code change.
6. **Production checklist** — strong `POSTGRES_PASSWORD`; TLS terminated by a reverse proxy in front of
   port 3000 (operator's choice); set `API_CORS_ORIGINS` to the public origin; keep ports on localhost
   or a private network; backups of `pgdata` (`docker compose exec db pg_dump ...`); the API rate limit
   (`COMPUTE_REQUESTS_PER_MINUTE`) is per process — use a shared limiter for several API instances;
   logs are JSON on stdout without query strings or secrets.
7. **Verification** — the exact checks the CI `docker` job runs, and `pnpm smoke` against the API.
8. **Troubleshooting** — api unhealthy (logs: `docker compose logs api`), database not ready, port in use,
   "Model not trained" (run train), demo banner still shown (run a live sync).
