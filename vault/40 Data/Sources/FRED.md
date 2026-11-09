---
type: source
publisher: Federal Reserve Bank of St. Louis
api_key_required: true
verified_series: 7
latest_period: "2026-11-06"
probe_date: 2026-11-08
docs: https://fred.stlouisfed.org/docs/api/fred/series_observations.html
tags:
  - data/source
---

# FRED

Publisher: **Federal Reserve Bank of St. Louis** · [API documentation](https://fred.stlouisfed.org/docs/api/fred/series_observations.html) · API key: required for full API (server-side only)

## Verified by live probe (2026-11-08)
Verified via the key-free `fredgraph.csv` endpoint (values and dates only):

| Series | Use | Coverage |
| --- | --- | --- |
| `GDPC1` | US real GDP | 1947-01-01 – 2026-07-01 (319 obs) |
| `UNRATE` | Unemployment | 1948-01 – 2026-10 |
| `CPIAUCSL` | CPI index (inflation needs a transform) | 1947-01 – 2026-09 |
| `FEDFUNDS` | Policy rate | 1954-07 – 2026-10 |
| `T10Y3M` | Yield-curve slope | 1982-01-04 – 2026-11-06 |
| `USREC` | NBER reference (**not** the target) | 1854-12 – 2026-10 |
| `GFDEGDQ188S` | Federal debt % GDP | 1966 – 2026-04 |

Units, seasonal adjustment and ALFRED vintages need `FRED_API_KEY` (server-side) — not yet configured.

Evidence: `docs/data-feasibility-probe.json` · regenerate with `uv run python scripts/probe_sources.py --out docs/data-feasibility-probe.json`.
