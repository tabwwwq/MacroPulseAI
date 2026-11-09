---
type: source
publisher: European Central Bank
api_key_required: false
verified_series: 2
latest_period: "2026-09-16"
probe_date: 2026-11-08
docs: https://data.ecb.europa.eu/help/api/overview
tags:
  - data/source
---

# ECB

Publisher: **European Central Bank** · [API documentation](https://data.ecb.europa.eu/help/api/overview) · API key: not required

## Verified by live probe (2026-11-08)
| Series key | Meaning | Coverage |
| --- | --- | --- |
| `FM.B.U2.EUR.4F.KR.MRR_FR.LEV` | Main refinancing operations, fixed rate (date of changes) | 1999-01-01 – 2026-09-16 · 48 events |
| `FM.B.U2.EUR.4F.KR.DFR.LEV` | Deposit facility rate (date of changes) | 1999-01-01 – 2026-09-16 · 69 events |

Event-dated (changes on decision dates), unit `PCPA`. A **shared euro area rate** — never shown as a national rate for BE/DE/FR/NL ([[ADR-0007 Support levels are computed, never declared]]).

## Ingested by `data-sync` (2026-11-09)
The deposit facility rate is stored **once** as series `…:EA` (69 decision dates, 1999-01-01 → 2026-09-16; runs 1 and 4 `succeeded`) and served to each euro-area member with its scope note. The CSV `KEY` column must match the requested key, or the response is rejected. Event-dated series have no freshness age limit ([[ADR-0013 Native-series ingestion with quality gate]]).

Evidence: `docs/data-feasibility-probe.json` · regenerate with `uv run python scripts/probe_sources.py --out docs/data-feasibility-probe.json`.
