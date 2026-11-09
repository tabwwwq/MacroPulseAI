---
type: source
publisher: Eurostat (European Commission)
api_key_required: false
verified_series: 16
latest_period: "2026-Q3"
probe_date: 2026-11-08
docs: https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-introduction
tags:
  - data/source
---

# Eurostat

Publisher: **Eurostat (European Commission)** · [API documentation](https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-introduction) · API key: not required

## Verified by live probe (2026-11-08)
| Indicator | Dataset | Filter | Coverage (verified) |
| --- | --- | --- | --- |
| Real GDP (levels for q/q) | `namq_10_gdp` | `freq=Q, unit=CLV20_MNAC, s_adj=SCA, na_item=B1GQ` | BE 1995-Q1–2026-Q2 · DE 1991-Q1–2026-Q3 · FR 1980-Q1–2026-Q3 · NL 1996-Q1–2026-Q3 |
| Unemployment rate | `une_rt_m` | `s_adj=SA, age=TOTAL, sex=T, unit=PC_ACT` | BE/DE/FR/NL to 2026-09 |
| HICP annual rate | `prc_hicp_manr` | `coicop=CP00, unit=RCH_A` | ⚠️ ends 2025-12 — [[F-001 HICP dataset frozen at 2025-12]] |
| Gov. debt % GDP | `gov_10q_ggdebt` | `unit=PC_GDP, sector=S13, na_item=GD` | BE/DE/FR/NL/EA20 to 2026-Q2 |

Latest-revision data only (no vintages) → historical replays are labelled *revised-data / release-lag approximation*.
EA20 unemployment returned a multi-series response; EA GDP aggregate key not yet established.

Evidence: `docs/data-feasibility-probe.json` · regenerate with `uv run python scripts/probe_sources.py --out docs/data-feasibility-probe.json`.
