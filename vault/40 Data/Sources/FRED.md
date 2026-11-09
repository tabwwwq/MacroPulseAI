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

## Ingested by `data-sync` (2026-11-09)
7 series, **16,608 observations**, runs 3 and 6 `succeeded`, via the key-free `fredgraph.csv` endpoint. The CSV header must name the requested series, and quarterly/monthly dates must be period starts, or the series is rejected. FRED's `.` marks a missing value: it is skipped, counted and reported as a `source_warning` (485 in `T10Y3M`, one each in `CPIAUCSL` and `UNRATE` → [[F-006 US October 2025 observations missing]]). Units come from FRED documentation, so US mappings stay `partial` until the key-based metadata path exists.

Evidence: `docs/data-feasibility-probe.json` · regenerate with `uv run python scripts/probe_sources.py --out docs/data-feasibility-probe.json`.
