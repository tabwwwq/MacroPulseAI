# Brief: rewrite docs/DATA_FEASIBILITY.md from live probe evidence

## Context
Your previous run could not reach the network from your sandbox. The lead engineer has since run
`uv run python scripts/probe_sources.py --out docs/data-feasibility-probe.json` outside the sandbox
(CA bundle: certifi). That JSON now contains real HTTP evidence: 45 records, statuses
verified/partial/failed/unverified, request URLs, retrieval timestamps, periods, counts and
`response_labels` taken from the official responses.

## Files you may edit (only this one)
- `docs/DATA_FEASIBILITY.md` (rewrite completely)

Read-only inputs: `docs/data-feasibility-probe.json`, `scripts/probe_sources.py`, `CLAUDE.md`.
Python is not available in your sandbox: read the JSON with PowerShell (`ConvertFrom-Json`).

## Required content (every number must come from the JSON; cite nothing from memory)
1. Header: probe generation time (UTC), command to regenerate, CA bundle used.
2. Summary matrix: rows = indicators (real GDP q/q source series, unemployment, HICP inflation,
   policy rate, general-government debt % GDP, leading indicator (CLI), annual GDP growth, annual
   central-gov debt, yield spread, NBER reference); columns = BE, DE, FR, NL, US, EA.
   Cell = status + last period (e.g. `verified · 2026-Q3`), or `n/a` where the source does not apply.
3. Per-source sections (Eurostat, ECB, FRED, World Bank, OECD) with the exact dataset codes /
   series keys / filters that were verified and one example request URL each.
4. Key findings, at least:
   - Eurostat `namq_10_gdp` unit and s_adj that were verified, and per-country first/last quarter.
   - `prc_hicp_manr` last period vs. dataset `updated` timestamp → treat as possibly discontinued;
     a successor dataset must be identified and verified in Phase 3 (do not name one unless the
     JSON shows it).
   - OECD CLI (`LI`) availability per country from `response_labels` (note which countries only
     expose confidence indicators).
   - World Bank central-government debt sparsity vs. Eurostat general-government quarterly debt.
   - ECB rates are event-dated and are a shared euro area rate, not national rates.
   - FRED: values verified via fredgraph CSV; units/SA/vintages need `FRED_API_KEY` (ALFRED).
   - Euro area aggregate results (which EA rows failed and why).
5. Proposed support level per country with justification from the evidence
   (`full` = verified quarterly real GDP + inflation + unemployment from a current, non-stale series).
   If HICP is stale, say what that implies (e.g. `full` pending a current HICP series).
6. Caveats: latest-revision data (no Eurostat vintages), release-lag assumptions are NOT verified by
   this probe (label them "assumption, to verify"), unit comparability notes.

Keep it concise and scannable (tables > prose). No marketing language.
