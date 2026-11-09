---
type: source
publisher: Eurostat (European Commission)
api_key_required: false
verified_series: 16
ingested_observations: 4417
last_sync: 2026-11-09
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
| HICP annual rate | ~~`prc_hicp_manr`~~ → **`prc_hicp_minr`** | `freq=M, unit=RCH_A, coicop18=TOTAL` | BE/DE/FR/NL 1997-01–2026-10 (successor verified 2026-11-09; the old dataset ends 2025-12 — [[F-001 HICP dataset frozen at 2025-12]]) |
| Gov. debt % GDP | `gov_10q_ggdebt` | `unit=PC_GDP, sector=S13, na_item=GD` | BE/DE/FR/NL/EA20 to 2026-Q2 |

## Ingested by `data-sync` (2026-11-09)
16 native series, **4,417 observations**, runs 2 and 5 `succeeded`. Each JSON-stat response must select exactly one series (every non-time dimension of size 1) or it is rejected. Eurostat status flags (`p` provisional, `e` estimated, `b` break) are stored per observation, and the dataset `updated` stamp is kept as `source_updated_at` (not a publication date). Connector: `packages/economics/src/macropulse_economics/connectors/eurostat.py` · [[ADR-0013 Native-series ingestion with quality gate]].

Latest-revision data only (no vintages) → historical replays are labelled *revised-data / release-lag approximation*.
EA20 unemployment returned a multi-series response; EA GDP aggregate key not yet established.

Evidence: `docs/data-feasibility-probe.json` · regenerate with `uv run python scripts/probe_sources.py --out docs/data-feasibility-probe.json`.
