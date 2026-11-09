---
type: decision
id: ADR-0005
date: 2026-11-08
status: accepted
area: architecture
tags:
  - decision
---

# ADR-0005 · Next.js proxies the API

> [!decision] Decision
> Next.js rewrites `/api/*` to `API_URL` server-side; the browser always calls same-origin `/api`.

## Context
The browser should not need to know the backend URL, and CORS should stay strict.

## Consequences
No backend URL in the client bundle; FastAPI CORS still allows explicit origins only. In Docker the proxy target is baked at build time (`API_URL` build arg).
