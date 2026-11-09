---
type: source
publisher: OECD
api_key_required: false
verified_series: 0
latest_period: "2026-09"
probe_date: 2026-11-08
docs: https://data-explorer.oecd.org/
tags:
  - data/source
---

# OECD

Publisher: **OECD** · [API documentation](https://data-explorer.oecd.org/) · API key: not required

## Verified by live probe (2026-11-08)
Dataflow `OECD.SDD.STES,DSD_STES@DF_CLI,4.1` (monthly). Latest-observation slices only:

| Country | Composite leading indicator (`LI`) | Other series |
| --- | --- | --- |
| DE, FR, US | ✅ available (AA / NOR / TR variants) | confidence, components |
| BE, NL | ❌ not published | business & consumer confidence only |

See [[F-002 OECD CLI missing for Belgium and Netherlands]]. Exact measure/adjustment and history to be fixed in Phase 3.

Evidence: `docs/data-feasibility-probe.json` · regenerate with `uv run python scripts/probe_sources.py --out docs/data-feasibility-probe.json`.
