---
type: source
publisher: The World Bank
api_key_required: false
verified_series: 9
latest_period: "2025"
probe_date: 2026-11-08
docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
tags:
  - data/source
---

# World Bank

Publisher: **The World Bank** · [API documentation](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392) · API key: not required

## Verified by live probe (2026-11-08)
| Indicator | Coverage |
| --- | --- |
| `NY.GDP.MKTP.KD.ZG` annual GDP growth | BE/DE/FR/NL/US 1961–2025 (65 obs each) |
| `GC.DOD.TOTL.GD.ZS` central-gov debt % GDP | Sparse: BE 0, DE 1, FR 0, NL 5, US 36 obs — [[F-004 World Bank central-government debt is sparse]] |

Annual only; never presented as quarterly updates. Licence CC BY 4.0.

Evidence: `docs/data-feasibility-probe.json` · regenerate with `uv run python scripts/probe_sources.py --out docs/data-feasibility-probe.json`.
