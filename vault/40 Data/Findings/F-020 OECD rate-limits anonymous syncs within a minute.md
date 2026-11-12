---
type: finding
id: F-020
severity: low
status: resolved
area: data
found: 2026-11-12
tags:
  - finding
---

# F-020 · OECD rate-limits anonymous syncs within a minute

> [!finding] Low · resolved
> Second `macropulse data-sync --source oecd` about 40 s after the first (run 14): `USA.M.BCICP…` and `USA.M.LI…` failed with **HTTP 429** after 4 attempts; the run was stored as `partial` and the earlier rows stayed (nothing deleted). About 26 requests had reached `sdmx.oecd.org` within roughly a minute, counting the probes. The 429 carried no usable `Retry-After`, so the default backoff (1.5 + 3 + 6 s) was far too short for a per-minute window.

## Action
- `HOST_MIN_INTERVAL_S = {"sdmx.oecd.org": 3.5}`: at most ~17 requests a minute from one sync.
- `RATE_LIMIT_WAIT_S = 30`: a 429 without `Retry-After` waits out the window instead of burning retries.
- Verified: run 15 fetched all 13 OECD series (9,375 observations) in 45 s without a 429. Two unit tests cover the spacing and the wait.

Related: [[ADR-0027 OECD connector with confidence indicators kept apart from the CLI]]
