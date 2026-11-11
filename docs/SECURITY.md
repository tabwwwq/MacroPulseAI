# Security and release audit

Audit performed for the Phase 10 release on 2026-11-11 (Windows 11 development machine; CI on GitHub
Actions `ubuntu-latest`). Every line below states what was checked and how; nothing here is a claim
that was not run. The checks marked **CI** run on every push.

## Results

| Area | What was checked | Result |
|---|---|---|
| Secrets in git history | `scripts/security_scan.py --history`: token formats (GitHub, AWS, OpenAI, Anthropic, Google, Slack), private keys, secret assignments, database URLs with passwords, over every added line of every commit — **CI** | 0 findings; 2 reviewed false positives (fake keys in redaction tests) listed with reasons in `.security-scan-allow` |
| Secrets in tracked files | same scanner over `git ls-files` — **CI** | 0 findings (same 2 reviewed test values) |
| Client bundle | scanner over `apps/web/.next/static` after `next build`: token formats plus server-only names (`FRED_API_KEY`, `DATABASE_URL`, `POSTGRES_PASSWORD`) — **CI** | 0 findings |
| `FRED_API_KEY` | where it is read and sent | Server-side `SecretStr`; only "configured: yes/no" is exposed. The current FRED connector uses the public CSV endpoint and never sends the key |
| Credentials in provenance | request URLs are stored and exported (API, PDF/CSV reports) | `redact_secrets` masks `api_key`/`token`/`key`/`password` query parameters and URL passwords before storage, also in error summaries and quality-check details; tested end to end (`test_hardening.py`) |
| Dependencies | `pip-audit 2.10.1` on the 49 pinned production Python packages (`uv export --frozen`); `pnpm audit --prod` on the 144 production web packages — **CI** | No known vulnerabilities |
| CORS | `API_CORS_ORIGINS` | Explicit origins only; a wildcard is rejected at start-up; credentials disabled; the browser uses the same-origin Next.js proxy |
| Input validation | every query parameter has a pattern or bound; request bodies are Pydantic models with `extra="forbid"` and bounded fields | Invalid input → `422` with the structured error contract (tested per endpoint) |
| Request size | middleware | `POST`/`PUT`/`PATCH` need `Content-Length`; bodies over 64 KiB → `413`, unsized → `411` (tested) |
| Query safety | SQLAlchemy ORM / bound parameters | The only textual SQL is the constant `SELECT 1` readiness probe |
| Expensive operations | forecasts, scenarios, reports | In-process rate limit (`COMPUTE_REQUESTS_PER_MINUTE`, default 240 per client address, `429` + `Retry-After`); no sync/train endpoints exist (CLI only); no URL fetching from user input; no uploads |
| Logs | request middleware, connectors | One JSON line per request with the **path only** (no query strings), validated request ids, error classes instead of messages for unexpected failures; connector errors carry the host, not the URL |
| Exports | PDF / CSV / JSON reports, raw observation CSV | Filenames built from validated country/as-of; renderer failures → `500 report_generation_failed` with a request id and no internals (tested with a path and a key name in the exception); exported values come from official sources, not user input |
| HTTP headers (API) | every response | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `X-Request-ID` (tested) |
| HTTP headers (web) | `next.config.ts` | `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`; production **Content-Security-Policy**: `default-src 'self'`, no third-party origins, `frame-ancestors 'none'`, `object-src 'none'` (`'unsafe-inline'` is needed for Next.js inline bootstrap). The full E2E suite runs against the production build with this policy and records no console errors |
| Containers | `apps/api/Dockerfile`, `apps/web/Dockerfile`, `compose.yml` | Non-root users (`app`, `node`); ports bound to `127.0.0.1`; no secrets baked into images; the API image runs migrations on start — **CI** builds and starts the stack against PostgreSQL |

## Accessibility (part of the same release audit)

`axe-core` (WCAG 2.0/2.1 A and AA rules) runs on every page at 1440 px and 375 px in the Playwright
suite — **CI**. The first run found and the release fixed: insufficient contrast of primary buttons
(white on `#2f9bff`, about 2.9:1 → dark text on `#4cc3ff`, about 9:1), subtle text on tinted rows
(token lightened to `#8a95ad`), eleven horizontally scrollable tables not reachable by keyboard (now
focusable regions), and a link inside running text identified by colour only. Current result: no
serious or critical violations on any page.

## Known limits

- The rate limit is per process; several API instances need a shared limiter (documented in
  `docs/DEPLOY.md`).
- `'unsafe-inline'` in `script-src` remains (Next.js without nonces).
- No authentication: the app serves public statistics read-only; there are no user accounts or
  write endpoints other than the bounded compute endpoints above.
- TLS, backups and the secrets store are the operator's responsibility (`docs/DEPLOY.md`).
