---
type: finding
id: F-010
severity: medium
status: resolved
area: tooling
found: 2026-11-10
resolved: 2026-11-10
tags:
  - finding
---

# F-010 · Docker build broke when the ML package was added

> [!finding] Medium severity · resolved 2026-11-10
> GitHub Actions run 42667057588 for `ed7a1ab` (Phase 5) **failed in the "Docker images" job** (`docker compose build`); the API and web jobs passed. It had been reported as "still running" at the end of Phase 5 and not re-checked before Phase 6 started.

## Cause
`apps/api/Dockerfile` copied only `apps/api` and `packages/economics`; the new workspace member `packages/ml` (a dependency of the API) was missing. Reproduced without Docker by running the image's second `uv sync --frozen --no-dev --all-packages` on the same file set: `Distribution not found at: …/packages/ml`. With `packages/ml` copied the install succeeds and `macropulse_api`, `macropulse_ml` and scikit-learn import.

## Fix
The Dockerfile copies `packages/ml` (manifest and sources), creates `/app/models/artifacts` for the non-root user and sets `MODELS_DIR`; compose mounts a `models` volume. Verified by CI: run 42827449417 for `b6987da` passed all three jobs, including "Docker images" (`docker compose build`). Docker is still not installed on the development machine.

## Lesson
After every push, confirm the CI conclusion — not only that a run started.

Related: [[F-007 OneDrive locks the virtual environment]] · [[Phase 06 — Explainable risk dashboard & ML lab]]
