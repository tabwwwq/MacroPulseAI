# Demo snapshot — genuine official data, captured 2026-11-09

`snapshot-2026-11-09.json.gz` (108 KB) holds the **25,702 observations of 31 native series** that a
live `macropulse data-sync` stored on 2026-11-09 (last retrieval 17:26 UTC). It exists so the app can
be tried **offline and without any credentials**:

```powershell
pnpm demo        # install, migrate, load this snapshot, train, start the app
```

or step by step: `uv run macropulse demo-load` after `pnpm bootstrap`.

## What it is — and is not

- Values, status flags, request URLs, source update stamps and retrieval times are exactly what the
  sources returned on that day (a load into an empty database reproduces the stored rows exactly).
- Loading runs the normal sync pipeline (validation, quality checks) with ingestion runs marked
  `snapshot`. Data freshness is the **capture time**, never the import time, and the app shows a
  **DEMO banner** while snapshot data is in use.
- It is **not live**: it ages like any download. Run `pnpm data:sync` to replace it with current data
  (no keys needed for Eurostat, ECB and the FRED CSV endpoint).
- Nothing in it is synthetic or edited; tests use their own small fixtures.

## Contents and sources

| Source | Series (geo) | Terms and attribution |
|---|---|---|
| Eurostat | `namq_10_gdp` real GDP, chain-linked volumes, SCA (BE, DE, FR, NL); `prc_hicp_minr` HICP annual rate (BE, DE, FR, NL); `une_rt_m` unemployment rate, SA (BE, DE, FR, NL); `gov_10q_ggdebt` government debt % of GDP (BE, DE, FR, NL); `irt_lt_mcby_m` 10-year yields (BE, DE, FR, NL); `irt_st_m` 3-month rate (EA) | "Source: Eurostat." Reuse authorised with acknowledgement of the source — [Eurostat copyright policy](https://ec.europa.eu/eurostat/about-us/policies/copyright) |
| European Central Bank | `FM B.U2.EUR.4F.KR.DFR.LEV` deposit facility rate (euro area) | "Source: European Central Bank (ECB Data Portal)." — [ECB disclaimer and copyright](https://www.ecb.europa.eu/services/disclaimer/html/index.en.html) |
| FRED, Federal Reserve Bank of St. Louis | `GDPC1` (BEA), `CPIAUCSL`, `UNRATE` (BLS), `FEDFUNDS`, `GS10`, `TB3MS`, `T10Y3M` (Board of Governors), `GFDEGDQ188S` (OMB/FRB St. Louis), `USREC` (NBER-based recession indicator, external reference only) | Retrieved from FRED; each series remains subject to its original source's terms — [FRED legal](https://fred.stlouisfed.org/legal/) |

Each observation keeps the exact request URL it came from, so every number in the app can be traced
back to its source request (Data observatory → lineage).

## Regenerating

```powershell
pnpm data:sync
uv run macropulse demo-export --out data/demo/snapshot-YYYY-MM-DD.json.gz
```
Update `DEFAULT_SNAPSHOT` in `apps/api/src/macropulse_api/services/demo.py` and this file.
