# Data feasibility — live probe evidence

> **Update 2026-11-09 (Phase 3 ingestion).** The probe below is the 2026-11-08 snapshot and is kept as
> evidence. Since then:
> - The HICP blocker is **resolved**: successor dataset **`prc_hicp_minr`** (`freq=M`, `unit=RCH_A`,
>   `coicop18=TOTAL`, ECOICOP ver. 2) is live-verified for BE, DE, FR, NL from **1997-01 to 2026-10**
>   (358 months each). On the overlap with `prc_hicp_manr` the values differ by at most 0.1 pp.
> - `uv run macropulse data-sync` stored **21,094 observations** from 24 native series: Eurostat 16 series
>   / 4,417 rows, ECB 1 / 69, FRED 7 / 16,608. Every run succeeded.
> - Real gaps kept as gaps: US `CPIAUCSL` and `UNRATE` have no 2025-10 value (FRED `.`), and `T10Y3M` has
>   485 `.` days. Nothing is interpolated.
> - Computed support levels: BE, DE, FR, NL **full**; US **partial** (FRED units and metadata need the
>   key-based API).

- Probe generated (UTC): **2026-11-08T22:18:14.389483+00:00**.
- Evidence: [data-feasibility-probe.json](data-feasibility-probe.json); source-specific claims below refer to its `records`, including `request_url`, `retrieved_at_utc`, `notes` and `response_labels`.
- Regenerate: `uv run python scripts/probe_sources.py --out docs/data-feasibility-probe.json`.
- CA bundle used: **certifi**. The script falls back to system certificates if certifi is unavailable; check the output's `ca_bundle` before comparing runs.
- Recorded outcomes: **45 records** — **28 verified**, **14 partial**, **2 failed**, **1 unverified**. This document interprets the supplied probe; it does not report a new network run.

## Summary matrix

Statuses are copied from the probe: `verified` establishes the returned series, not freshness or production readiness; `partial` has missing metadata, limited scope or missing observations; `failed` rejected the response; `unverified` did not establish a unique key. `—` means no last period. `n/a` means no applicable source mapping in this probe, not proof that no official series exists.

| Indicator / source | BE | DE | FR | NL | US | EA |
|---|---|---|---|---|---|---|
| Real GDP q/q source series (Eurostat; FRED for US) | verified · 2026-Q2 | verified · 2026-Q3 | verified · 2026-Q3 | verified · 2026-Q3 | partial · 2026-07-01 | unverified · — |
| Unemployment (Eurostat; FRED for US) | verified · 2026-09 | verified · 2026-09 | verified · 2026-09 | verified · 2026-09 | partial · 2026-10-01 | failed · — |
| HICP inflation (Eurostat) | verified · 2025-12 | verified · 2025-12 | verified · 2025-12 | verified · 2025-12 | n/a | verified · 2025-12 |
| Policy rate (shared ECB; FRED for US) | verified · 2026-09-16 | verified · 2026-09-16 | verified · 2026-09-16 | verified · 2026-09-16 | partial · 2026-10-01 | verified · 2026-09-16 |
| General-government debt % GDP (Eurostat) | verified · 2026-Q2 | verified · 2026-Q2 | verified · 2026-Q2 | verified · 2026-Q2 | n/a | verified · 2026-Q2 |
| Leading indicator / CLI discovery (OECD) | partial · 2026-09† | partial · 2026-09 | partial · 2026-09 | partial · 2026-09† | partial · 2026-09 | n/a |
| Annual GDP growth (World Bank) | verified · 2025 | verified · 2025 | verified · 2025 | verified · 2025 | verified · 2025 | n/a |
| Annual central-government debt (World Bank) | partial · — | verified · 1990 | partial · — | verified · 1994 | verified · 2024 | n/a |
| Yield spread (FRED) | n/a | n/a | n/a | n/a | partial · 2026-11-06 | n/a |
| NBER reference (FRED) | n/a | n/a | n/a | n/a | partial · 2026-10-01 | n/a |

† BE and NL return confidence indicators only, with no `LI` in the returned labels; these cells do **not** verify CLI availability. Policy-rate national cells reuse the EA records, not separate national requests. Both ECB rates have the same last date. US inflation candidate `CPIAUCSL` is `partial · 2026-09-01`, outside the HICP row; US federal-debt candidate `GFDEGDQ188S` is `partial · 2026-04-01`, outside the general-government row. Neither is a verified comparable substitute.

## Eurostat

Filters below are exact recorded selections; `geo` varies as listed and every request includes `lang=EN`. Omitted dimensions were not explicitly filtered.

| Dataset | Exact filters excluding geo/lang | Validated geography / meaning |
|---|---|---|
| `namq_10_gdp` | `freq=Q`, `unit=CLV20_MNAC`, `s_adj=SCA`, `na_item=B1GQ` | BE, DE, FR, NL: quarterly real GDP source levels |
| `une_rt_m` | `s_adj=SA`, `age=TOTAL`, `sex=T`, `unit=PC_ACT` | BE, DE, FR, NL: monthly; total age/sex; percentage of population in the labour force; seasonally adjusted, not calendar adjusted |
| `prc_hicp_manr` | `coicop=CP00`, `unit=RCH_A` | BE, DE, FR, NL, EA20: monthly all-items HICP, annual rate of change |
| `gov_10q_ggdebt` | `unit=PC_GDP`, `sector=S13`, `na_item=GD` | BE, DE, FR, NL, EA20: quarterly general-government consolidated gross debt, percentage of GDP |

Example recorded request: [BE real GDP](https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/namq_10_gdp?freq=Q&unit=CLV20_MNAC&s_adj=SCA&na_item=B1GQ&geo=BE&lang=EN).

### GDP history

The verified unit is `CLV20_MNAC` and adjustment is `SCA`. GDP records retain these codes rather than `response_labels`; do not infer additional unit metadata from this snapshot. These are source levels for deriving q/q growth, not a verified precomputed q/q growth series. The probe did not calculate growth or recession labels.

| Country | First quarter | Last quarter | Nonmissing observations |
|---|---|---|---|
| BE | 1995-Q1 | 2026-Q2 | 126 |
| DE | 1991-Q1 | 2026-Q3 | 143 |
| FR | 1980-Q1 | 2026-Q3 | 187 |
| NL | 1996-Q1 | 2026-Q3 | 123 |

The US Eurostat request with the same filters and `geo=US` failed: “Response is not a single series with time as final dimension.” The US matrix cell uses partial FRED evidence instead.

### Inflation freshness and euro area aggregate

All verified `prc_hicp_manr` country/aggregate records end at **2025-12**, while their notes give dataset `updated` **2026-02-06T23:00:00+0100**. At probe generation this is stale and **possibly discontinued**; an update timestamp is not a new observation period. **Phase 3 must identify and verify a current successor dataset** before current inflation or full support is claimed. No successor is identified by this JSON.

| EA record | Result | Evidence / limitation |
|---|---|---|
| Real GDP | unverified | EA aggregate not uniquely discovered in metadata slice; no exact aggregate key established |
| Unemployment, `geo=EA20` | failed | “Response is not a single series”; this is a response-shape failure, not proof of unavailable data |
| HICP, `geo=EA20` | verified, stale | Last 2025-12; response geography label is “Euro area – 20 countries (2023-2025)” |
| Quarterly debt, `geo=EA20` | verified | 2000-Q1–2026-Q2; 106 observations; same geography label |
| ECB policy rates | verified | Shared EA rates; see below |

Neither GDP nor unemployment failure establishes an HTTP outage: their recorded HTTP status is `200`. Aggregate composition must be reconciled before combining EA20 statistics with ECB's `U2` rates.

## ECB

| Exact series key | Response title | First / last event date | Observations |
|---|---|---|---|
| `FM.B.U2.EUR.4F.KR.MRR_FR.LEV` | Main refinancing operations - fixed rate tenders (fixed rate) (date of changes) - Level | 1999-01-01 / 2026-09-16 | 48 |
| `FM.B.U2.EUR.4F.KR.DFR.LEV` | Deposit facility - date of changes (raw data) - Level | 1999-01-01 / 2026-09-16 | 69 |

Both are verified, with recorded frequency `B` and unit `PCPA`. They are **event-dated** (changes on decision dates), not regular monthly observations. The last event date alone does not establish staleness. Assign them as a **shared euro area policy rate**, never as independently observed national rates. Calendar alignment and the choice of policy-rate feature remain connector decisions.

Example recorded request: [ECB deposit facility](https://data-api.ecb.europa.eu/service/data/FM/B.U2.EUR.4F.KR.DFR.LEV?format=csvdata&detail=full).

## FRED

Exact filter for each request: `id=<series>` via fredgraph CSV. Every series below is **partial**: numeric values and dates were verified, but frequency, units and seasonal adjustment are null in the evidence.

| Series | Probe indicator | First date | Last date | Nonmissing observations |
|---|---|---|---|---|
| `GDPC1` | real_gdp | 1947-01-01 | 2026-07-01 | 319 |
| `UNRATE` | unemployment | 1948-01-01 | 2026-10-01 | 945 |
| `CPIAUCSL` | inflation | 1947-01-01 | 2026-09-01 | 956 |
| `FEDFUNDS` | policy_rate | 1954-07-01 | 2026-10-01 | 868 |
| `T10Y3M` | yield_spread | 1982-01-04 | 2026-11-06 | 11215 |
| `USREC` | nber_reference | 1854-12-01 | 2026-10-01 | 2063 |
| `GFDEGDQ188S` | federal_debt | 1966-01-01 | 2026-04-01 | 242 |

Example recorded request: [FRED GDPC1 CSV](https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPC1).

Official units/frequency/SA metadata and ALFRED vintages/release dates need the server-side `FRED_API_KEY` validation path; they were **not probed**. Do not interpret date spacing as verified frequency or treat the inflation candidate as a verified HICP-equivalent annual rate. Keep `USREC` as an external NBER reference, separate from GDP-based technical-recession labels.

## World Bank

Exact request selections: `country=BE|DE|FR|NL|US`, `indicator=<code>`, with `format=json&per_page=1000`. No EA aggregate was probed.

| Indicator code | Verified response unit/name | Coverage |
|---|---|---|
| `NY.GDP.MKTP.KD.ZG` | GDP growth (annual %) | Each of BE, DE, FR, NL, US: verified; 1961–2025; 65 nonmissing observations |
| `GC.DOD.TOTL.GD.ZS` | Central government debt, total (% of GDP) | Sparse; see below |

Example recorded request: [US central-government debt](https://api.worldbank.org/v2/country/US/indicator/GC.DOD.TOTL.GD.ZS?format=json&per_page=1000).

| Country | Central debt status | First / last year | Nonmissing observations |
|---|---|---|---|
| BE | partial | — / — | 0 |
| DE | verified | 1990 / 1990 | 1 |
| FR | partial | — / — | 0 |
| NL | verified | 1990 / 1994 | 5 |
| US | verified | 1989 / 2024 | 36 |

A verified historical response can still be unusably stale. Prefer the verified Eurostat quarterly **general-government** debt for the European fiscal feature: BE 1995-Q4–2026-Q2 (123 observations); DE, FR, NL each 2000-Q1–2026-Q2 (106). World Bank **central-government** scope differs; do not splice the series or present annual observations as quarterly updates. Annual GDP growth cannot replace the quarterly real GDP target.

## OECD

Recorded flow: `OECD.SDD.STES,DSD_STES@DF_CLI,4.1`; exact country slices below use `lastNObservations=1&format=csvfilewithlabels`. These are verified response slices with **partial** status, not fixed production CLI keys or historical coverage checks.

| Country | Exact slice key | `LI` in `response_labels.series`? | Returned observations | Last period across slice |
|---|---|---|---|---|
| BE | `BEL.M.......` | No; only `BCICP` and `CCICP` | 2 | 2026-09 |
| DE | `DEU.M.......` | Yes | 17 | 2026-09 |
| FR | `FRA.M.......` | Yes | 17 | 2026-09 |
| NL | `NLD.M.......` | No; only `BCICP` and `CCICP` | 2 | 2026-09 |
| US | `USA.M.......` | Yes | 16 | 2026-09 |

Example recorded request: [OECD Germany slice](https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_CLI,4.1/DEU.M.......?lastNObservations=1&format=csvfilewithlabels).

For DE, FR and US the labels explicitly include `LI / Composite leading indicator (CLI)` with `AA / Amplitude adjusted / IX / Index`, `NOR / Normalized / IX / Index`, and `TR / Trend restored` with either `GY / Growth rate, over 1 year` or `IX / Index`. BE and NL expose only composite business confidence (`BCICP`) and composite consumer confidence (`CCICP`), both `AA / Amplitude adjusted / IX / Index`, in these slices. Do not relabel confidence as CLI or generalize absence beyond the queried slices. Counts span multiple series; the last period is the slice maximum, not a proven common endpoint for every variant. Phase 3 must fix measure/adjustment/transformation and verify history and comparability.

## Proposed country support

`full` requires verified quarterly real GDP, inflation and unemployment from current, non-stale series. These are evidence-based proposals for source support, not claims that connectors or models work.

| Country | Proposed level now | Justification / condition for full |
|---|---|---|
| BE | partial | Verified GDP through 2026-Q2 and unemployment through 2026-09; full pending a current HICP series; CLI not established |
| DE | partial | Verified GDP through 2026-Q3 and unemployment through 2026-09; full pending a current HICP series; CLI history/key still partial |
| FR | partial | Verified GDP through 2026-Q3 and unemployment through 2026-09; full pending a current HICP series; CLI history/key still partial |
| NL | partial | Verified GDP through 2026-Q3 and unemployment through 2026-09; full pending a current HICP series; CLI not established |
| US | partial | Core FRED values returned, but quarterly frequency, units, adjustment and inflation transformation remain unverified; validate metadata before full |
| EA | partial | Debt and shared rates verified; GDP aggregate key unverified, unemployment response rejected, HICP stale; target-dependent features unavailable |

## Caveats and verification gates

| Topic | Constraint / follow-up |
|---|---|
| Revisions / as-of history | Eurostat returns latest-revision history; no Eurostat vintages were verified. Historical replay must be labelled revised-data / release-lag approximation, not true point-in-time evidence. ALFRED vintage access remains unverified. |
| Release lags | **Assumption, to verify:** any GDP, inflation, unemployment or debt publication lag, availability calendar or within-quarter alignment rule. This probe verifies neither historical release dates nor numeric lag assumptions. Retrieval timestamps and dataset update timestamps are not observation publication dates. |
| Units / transforms | GDP levels require validated q/q transformation and adjacent nonmissing quarters. Preserve `CLV20_MNAC`/`SCA`; check FRED metadata before comparing. HICP annual change is not interchangeable with an unvalidated inflation candidate. Percentage of labour force, percentage of GDP, annual growth, index and rate features need distinct definitions. |
| Scope / frequency | Central, federal and general-government debt are distinct scopes. Annual GDP growth is not quarterly GDP growth. Event-dated ECB rates need explicit alignment; OECD index and growth variants must not be mixed. |
| Missingness / counts | Counts are nonmissing observations in the requested response, not guarantees of uninterrupted history. Missing data stays null/N/A with a reason; no silent imputation. OECD latest-observation slices do not establish usable training history. |
| Operational readiness | A successful recorded response does not verify scheduled refreshes, connector robustness, licensing, model training or predictions. Recheck stale series and failed mappings in Phase 3. |
