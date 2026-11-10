---
type: decision
id: ADR-0018
date: 2026-11-10
status: accepted
area: ml
tags:
  - decision
---

# ADR-0018 · Scenario lab as bounded model sensitivity

> [!decision] Decision
> A scenario adds bounded shocks to the published model's **latest as-of inputs** through a fixed, documented mapping and re-scores them with the published artifact. It answers "how does this model respond?", never "what would the economy do?" — every response and the page carry the disclaimer *Exploratory model sensitivity analysis, not a causal economic simulation.*

## Mapping (mechanical, no second-round effects)
| Shock (bounds) | Inputs moved |
|---|---|
| GDP growth ±5 pp | latest q/q and y/y growth; negative-quarter count recomputed |
| Inflation ±5 pp | inflation level and its six-month change |
| Unemployment ±4 pp | unemployment level and its six-month change |
| Policy rate ±4 pp | policy rate, its four-quarter change; term spread falls by the same amount |
| 10-year yield ±3 pp | term spread |

## Plausibility checks
- Per input: outside the training min/max (extrapolation) or outside the 5th–95th percentile (unusual).
- Jointly: squared Mahalanobis distance from the training mean with the training covariance (stored at training since run `20261110T142434Z`), against the χ²(11) 99 % quantile. Shocks that are each plausible can still form an implausible combination.

## Other choices
- **No server-side persistence** (`scenario_runs` not created): evaluation is cheap and stateless. Saved scenarios live in the browser's localStorage with the model version; export is JSON with request, result and disclaimer. The URL carries country, as-of, horizon and shocks.
- Request bodies are strict (`extra="forbid"`, bounds per shock); 350 ms client debounce.
- Forecast and scenario endpoints share an **in-process rate limit** (`COMPUTE_REQUESTS_PER_MINUTE`, default 240 per client address, 429 + `Retry-After`). Behind the same-origin proxy this is an app-wide budget; a shared limiter is left for multi-instance deployment (Phase 10).

## Consequences
The lab exposes model behaviour, including behaviour an economist would question — see [[F-012 Recession model lowers risk when unemployment rises]]. That is the point of sensitivity analysis and is stated rather than tuned away.

Related: [[ADR-0016 Inference serving and explanations]] · [[ADR-0017 Forecasts from rolling-origin backtests]] · [[Phase 07 — Forecasts & scenario lab]]
