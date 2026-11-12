---
type: codex-run
name: local-oecd-connector
date: 2026-11-12
time: "15:26"
status: success
exit_code: 0
sandbox: local-single-file
network: false
tags:
  - agent/codex
---

# ✅ Codex · local-oecd-connector

Delegated by Claude Code via `scripts/agents/codex-task.ps1` on 2026-11-12 15:26. Sandbox `local-single-file`, network off, exit code 0.
See [[Agent workflow]] for how delegation and review work.

> [!summary] Codex report
> ```python
> """OECD Data Explorer SDMX REST connector (Composite leading indicators dataflow, CSV output).
>
> Docs: https://data-explorer.oecd.org/
> Anonymous access is rate-limited, so the shared Fetcher's per-host throttle and 429 handling apply.
> The composite leading indicator exists only for some countries (BE and NL publish confidence
> indices only, finding F-002).
> """
>
> from __future__ import annotations
>
> import csv
> import io
> from datetime import UTC, datetime
>
> from macropulse_economics.connectors.base import (
>     ConnectorError,
>     FetchedObservation,
>     FetchResult,
>     SeriesRequest,
> )
> from macropulse_economics.connectors.http import Fetcher
> from macropulse_economics.periods import PeriodError, period_start
>
> BASE = "https://sdmx.oecd.org/public/rest/data"
> AGENCY = "OECD.SDD.STES"
> VERSIONS: dict[str, str] = {"DSD_STES@DF_CLI": "4.1"}  # dataflow -> version, verified 2026-11-12
> KEY_DIMENSIONS: tuple[str, ...] = (
>     "REF_AREA",
>     "FREQ",
>     "MEASURE",
>     "UNIT_MEASURE",
>     "ACTIVITY",
>     "ADJUSTMENT",
>     "TRANSFORMATION",
>     "TIME_HORIZ",
>     "METHODOLOGY",
> )
>
>
> def parse_csv(text: str, request: SeriesRequest) -> tuple[list[FetchedObservation], str | None]:
>     reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
>     rows = list(reader)
>     if not rows:
>         raise ConnectorError(f"OECD {request.dataset}.{request.series_key}: empty response")
>
>     header = reader.fieldnames or []
>     missing = [name for name in ("TIME_PERIOD", "OBS_VALUE", *KEY_DIMENSIONS) if name not in header]
>     if missing:
>         raise ConnectorError(f"OECD {request.dataset}.{request.series_key}: missing column {missing}")
>
>     parts = request.series_key.split(".")
>     if len(parts) != len(KEY_DIMENSIONS):
>         raise ConnectorError(
>             f"OECD {request.dataset}.{request.series_key}: series key must have "
>             f"{len(KEY_DIMENSIONS)} dimensions, got {len(parts)}"
>         )
>
>     observations: list[FetchedObservation] = []
>     seen_periods: set[str] = set()
>     unit: str | None = None
>     for row in rows:
>         key = ".".join((row.get(name) or "").strip() for name in KEY_DIMENSIONS)
>         if key != request.series_key:
>             raise ConnectorError(
>                 f"OECD {request.dataset}.{request.series_key}: unexpected series {key}"
>             )
>
>         mult = (row.get("UNIT_MULT") or "").strip()
>         if mult not in ("", "0"):
>             raise ConnectorError(
>                 f"OECD {request.dataset}.{request.series_key}: unit multiplier {mult!r} not supported"
>             )
>
>         raw = (row.get("OBS_VALUE") or "").strip()
>         if not raw:
>             continue
>         period = (row.get("TIME_PERIOD") or "").strip()
>         try:
>             period_start(period)
>             value = float(raw)
>         except (PeriodError, ValueError) as exc:
>             raise ConnectorError(
>                 f"OECD {request.dataset}.{request.series_key}: bad observation {period!r}={raw!r}"
>             ) from exc
>         if period in seen_periods:
>             raise ConnectorError(
>                 f"OECD {request.dataset}.{request.series_key}: duplicate period {period}"
>             )
>         seen_periods.add(period)
>         if unit is None:
>             unit = (row.get("UNIT_MEASURE") or "").strip() or None
>         observations.append(
>             FetchedObservation(period, value, (row.get("OBS_STATUS") or "").strip() or None)
>         )
>
>     observations.sort(key=lambda o: period_start(o.period))
>     return observations, unit
>
>
> def fetch(fetcher: Fetcher, request: SeriesRequest) -> FetchResult:
>     version = VERSIONS.get(request.dataset)
>     if version is None:
>         raise ConnectorError(f"OECD {request.dataset}: unknown OECD dataflow")
>     url = f"{BASE}/{AGENCY},{request.dataset},{version}/{request.series_key}"
>     response = fetcher.get(url, params={"format": "csvfile"})
>     observations, unit = parse_csv(response.text, request)
>     return FetchResult(
>         request=request,
>         observations=observations,
>         url=str(response.url),
>         retrieved_at=datetime.now(UTC),
>         unit_label=unit,
>     )
> ```
>
> - Unit is taken from the first row that carries a non-empty `UNIT_MEASURE` (all rows in the fixtures share it, so this matches the "first row" intent while staying robust).
> - The dimension-count check runs before any row values are read, per rule 3.
> - `UNIT_MULT` is validated for every row (including empty-value rows) so a bad multiplier is always rejected, matching the parametrized test.
> - `obs_status` is normalized to `None` when blank, and observations are sorted by `period_start` after parsing.
> - `fetch` raises on unknown dataflows before any HTTP request, and records `str(response.url)` plus a UTC `retrieved_at` for provenance.

> [!quote]- Brief sent to Codex
> # Brief
>
> Task: write the OECD SDMX connector (Composite leading indicators dataflow, CSV output).
>
> ## Files
> - CREATE `packages/economics/src/macropulse_economics/connectors/oecd.py` — the only file you write.
> - CONTEXT (provided below, do not change): `packages/economics/tests/test_oecd.py` (the specification —
>   read every assertion), the two fixtures it reads (genuine OECD responses),
>   `packages/economics/src/macropulse_economics/connectors/ecb.py` (the closest existing connector: copy its
>   structure and style), `connectors/base.py` (types), `connectors/http.py` (`Fetcher.get`).
>
> ## Public API (module-level)
>     BASE = "https://sdmx.oecd.org/public/rest/data"
>     AGENCY = "OECD.SDD.STES"
>     VERSIONS: dict[str, str] = {"DSD_STES@DF_CLI": "4.1"}   # dataflow -> version, verified 2026-11-12
>     KEY_DIMENSIONS: tuple[str, ...] = ("REF_AREA", "FREQ", "MEASURE", "UNIT_MEASURE", "ACTIVITY",
>                                        "ADJUSTMENT", "TRANSFORMATION", "TIME_HORIZ", "METHODOLOGY")
>     def parse_csv(text: str, request: SeriesRequest) -> tuple[list[FetchedObservation], str | None]: ...
>     def fetch(fetcher: Fetcher, request: SeriesRequest) -> FetchResult: ...
>
> ## parse_csv rules (every error is a `ConnectorError` whose message starts with "OECD " and names the key)
> 1. Strip a leading BOM ("﻿"), read with `csv.DictReader`. No rows → message contains "empty response".
> 2. The header must contain TIME_PERIOD, OBS_VALUE and every name in KEY_DIMENSIONS; otherwise the message
>    contains "missing column" and the missing names.
> 3. `request.series_key.split(".")` must have exactly `len(KEY_DIMENSIONS)` parts, else the message contains
>    "dimensions" (check this before reading rows' values).
> 4. For every row, the KEY_DIMENSIONS values joined with "." must equal `request.series_key`; otherwise the
>    message contains "unexpected series" and the offending key.
> 5. `UNIT_MULT` must be empty or "0" (values are published in units); anything else → "unit multiplier".
> 6. Empty OBS_VALUE → skip the row (never fill). Otherwise `float(value)` and `period_start(period)` must
>    succeed, else "bad observation" with the period and raw value (catch `PeriodError` and `ValueError`).
> 7. A period that appears twice → "duplicate period".
> 8. `obs_status` = stripped OBS_STATUS or None. Sort by `period_start(period)`.
> 9. Return `(observations, unit)` where unit = the first row's stripped UNIT_MEASURE or None.
>
> ## fetch
> `version = VERSIONS.get(request.dataset)`; None → `ConnectorError` containing "unknown OECD dataflow"
> (raise before any request). URL `f"{BASE}/{AGENCY},{request.dataset},{version}/{request.series_key}"`,
> `fetcher.get(url, params={"format": "csvfile"})`, then `FetchResult(request=request, observations=...,
> url=str(response.url), retrieved_at=datetime.now(UTC), unit_label=unit)`.
>
> Module docstring: OECD Data Explorer SDMX REST, docs https://data-explorer.oecd.org/ ; anonymous access is
> rate-limited, so the shared Fetcher's per-host throttle and 429 handling apply; the composite leading
> indicator exists only for some countries (BE and NL publish confidence indices only, finding F-002).
>
> ## Rules
> mypy --strict, ruff (line length 100), `from __future__ import annotations`, no new dependencies.
> Output only the file, in ONE fenced code block (three backticks, language python) — do not nest fences.
>
> # Output file
>
> `packages/economics/src/macropulse_economics/connectors/oecd.py`
>
> # Context files
>
> ## `packages/economics/tests/test_oecd.py`
>
> ```py
> """OECD SDMX connector (Composite leading indicators dataflow, CSV). Genuine responses, no network."""
>
> from __future__ import annotations
>
> from pathlib import Path
> from typing import Any
>
> import httpx
> import pytest
>
> from macropulse_economics.connectors import ConnectorError, SeriesRequest, fetch_series, oecd
> from macropulse_economics.connectors.http import Fetcher, make_client
>
> FIXTURES = Path(__file__).parent / "fixtures"
> USA_LI = SeriesRequest(
>     "oecd", "DSD_STES@DF_CLI", "USA.M.LI.IX._Z.AA.IX._Z.H", "US", "monthly", "index"
> )
> BEL_BCI = SeriesRequest(
>     "oecd", "DSD_STES@DF_CLI", "BEL.M.BCICP.IX._Z.AA.IX._Z.H", "BE", "monthly", "index"
> )
> HEADER = (
>     "DATAFLOW,REF_AREA,FREQ,MEASURE,UNIT_MEASURE,ACTIVITY,ADJUSTMENT,TRANSFORMATION,TIME_HORIZ,"
>     "METHODOLOGY,TIME_PERIOD,OBS_VALUE,OBS_STATUS,UNIT_MULT,DECIMALS,BASE_PER\n"
> )
> ROW = "OECD.SDD.STES:DSD_STES@DF_CLI(4.1),USA,M,LI,IX,_Z,AA,IX,_Z,H,{period},{value},A,{mult},2,\n"
>
>
> def _text(name: str) -> str:
>     return (FIXTURES / name).read_text(encoding="utf-8")
>
>
> def _csv(*rows: tuple[str, str], mult: str = "0") -> str:
>     return HEADER + "".join(ROW.format(period=p, value=v, mult=mult) for p, v in rows)
>
>
> def _fetcher(handler: Any) -> Fetcher:
>     return Fetcher(make_client(transport=httpx.MockTransport(handler)), sleep=lambda _s: None)
>
>
> def test_parses_the_cli_sorted_by_period_with_status_and_unit() -> None:
>     obs, unit = oecd.parse_csv(_text("oecd_cli_USA_LI_6.csv"), USA_LI)
>     assert [o.period for o in obs] == [
>         "1982-08",
>         "1982-09",
>         "2012-12",
>         "2013-01",
>         "2021-12",
>         "2022-01",
>     ]
>     assert obs[0].value == 96.57556
>     assert obs[-1].value == 101.0285
>     assert {o.obs_status for o in obs} == {"A"}
>     assert unit == "IX"
>
>
> def test_confidence_series_of_another_country() -> None:
>     obs, _ = oecd.parse_csv(_text("oecd_cli_BEL_BCICP_4.csv"), BEL_BCI)
>     assert [(o.period, o.value) for o in obs] == [
>         ("1993-09", 96.98607),
>         ("2011-11", 98.8876),
>         ("2016-02", 100.162),
>         ("2016-03", 100.3625),
>     ]
>
>
> def test_a_row_of_another_series_is_rejected() -> None:
>     with pytest.raises(ConnectorError, match="unexpected series"):
>         oecd.parse_csv(_text("oecd_cli_USA_LI_6.csv"), BEL_BCI)
>     mixed = _csv(("2026-01", "100.1")) + ROW.replace(",AA,", ",NOR,").format(
>         period="2026-02", value="100.2", mult="0"
>     )
>     with pytest.raises(ConnectorError, match="unexpected series"):
>         oecd.parse_csv(mixed, USA_LI)
>
>
> de
> …(truncated)
