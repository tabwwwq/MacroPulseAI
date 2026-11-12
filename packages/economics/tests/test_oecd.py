"""OECD SDMX connector (Composite leading indicators, CSV): genuine responses, no network."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pytest

from macropulse_economics.connectors import ConnectorError, SeriesRequest, fetch_series, oecd
from macropulse_economics.connectors.http import Fetcher, make_client

FIXTURES = Path(__file__).parent / "fixtures"
USA_LI = SeriesRequest(
    "oecd", "DSD_STES@DF_CLI", "USA.M.LI.IX._Z.AA.IX._Z.H", "US", "monthly", "index"
)
BEL_BCI = SeriesRequest(
    "oecd", "DSD_STES@DF_CLI", "BEL.M.BCICP.IX._Z.AA.IX._Z.H", "BE", "monthly", "index"
)
HEADER = (
    "DATAFLOW,REF_AREA,FREQ,MEASURE,UNIT_MEASURE,ACTIVITY,ADJUSTMENT,TRANSFORMATION,TIME_HORIZ,"
    "METHODOLOGY,TIME_PERIOD,OBS_VALUE,OBS_STATUS,UNIT_MULT,DECIMALS,BASE_PER\n"
)
ROW = "OECD.SDD.STES:DSD_STES@DF_CLI(4.1),USA,M,LI,IX,_Z,AA,IX,_Z,H,{period},{value},A,{mult},2,\n"


def _text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _csv(*rows: tuple[str, str], mult: str = "0") -> str:
    return HEADER + "".join(ROW.format(period=p, value=v, mult=mult) for p, v in rows)


def _fetcher(handler: Any) -> Fetcher:
    return Fetcher(make_client(transport=httpx.MockTransport(handler)), sleep=lambda _s: None)


def test_parses_the_cli_sorted_by_period_with_status_and_unit() -> None:
    obs, unit = oecd.parse_csv(_text("oecd_cli_USA_LI_6.csv"), USA_LI)
    assert [o.period for o in obs] == [
        "1982-08",
        "1982-09",
        "2012-12",
        "2013-01",
        "2021-12",
        "2022-01",
    ]
    assert obs[0].value == 96.57556
    assert obs[-1].value == 101.0285
    assert {o.obs_status for o in obs} == {"A"}
    assert unit == "IX"


def test_confidence_series_of_another_country() -> None:
    obs, _ = oecd.parse_csv(_text("oecd_cli_BEL_BCICP_4.csv"), BEL_BCI)
    assert [(o.period, o.value) for o in obs] == [
        ("1993-09", 96.98607),
        ("2011-11", 98.8876),
        ("2016-02", 100.162),
        ("2016-03", 100.3625),
    ]


def test_a_row_of_another_series_is_rejected() -> None:
    with pytest.raises(ConnectorError, match="unexpected series"):
        oecd.parse_csv(_text("oecd_cli_USA_LI_6.csv"), BEL_BCI)
    mixed = _csv(("2026-01", "100.1")) + ROW.replace(",AA,", ",NOR,").format(
        period="2026-02", value="100.2", mult="0"
    )
    with pytest.raises(ConnectorError, match="unexpected series"):
        oecd.parse_csv(mixed, USA_LI)


def test_empty_values_are_skipped_but_never_filled() -> None:
    obs, _ = oecd.parse_csv(
        _csv(("2026-01", "100.1"), ("2026-02", ""), ("2026-03", "99.9")), USA_LI
    )
    assert [o.period for o in obs] == ["2026-01", "2026-03"]


@pytest.mark.parametrize(
    ("text", "match"),
    [
        ("", "empty"),
        (HEADER, "empty"),
        ("TIME_PERIOD,OBS_VALUE\n2026-01,100\n", "column"),
        (_csv(("2026-01", "abc")), "bad observation"),
        (_csv(("2026-13", "100")), "bad observation"),
        (_csv(("2026-01", "100"), ("2026-01", "101")), "duplicate"),
        (_csv(("2026-01", "100"), mult="3"), "unit multiplier"),
    ],
)
def test_malformed_responses_are_errors(text: str, match: str) -> None:
    with pytest.raises(ConnectorError, match=match):
        oecd.parse_csv(text, USA_LI)


def test_a_key_with_the_wrong_number_of_dimensions_is_rejected() -> None:
    short = SeriesRequest("oecd", "DSD_STES@DF_CLI", "USA.M.LI", "US", "monthly", "index")
    with pytest.raises(ConnectorError, match="dimensions"):
        oecd.parse_csv(_text("oecd_cli_USA_LI_6.csv"), short)


def test_fetch_builds_the_versioned_dataflow_url_and_records_provenance() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, text=_text("oecd_cli_USA_LI_6.csv"))

    result = fetch_series(_fetcher(handler), USA_LI)
    assert seen[0].url.path == (
        "/public/rest/data/OECD.SDD.STES,DSD_STES@DF_CLI,4.1/USA.M.LI.IX._Z.AA.IX._Z.H"
    )
    assert seen[0].url.host == "sdmx.oecd.org"
    assert seen[0].url.params["format"] == "csvfile"
    assert result.url == str(seen[0].url)
    assert len(result.observations) == 6
    assert result.unit_label == "IX"
    assert result.retrieved_at.tzinfo is not None


def test_unknown_dataflows_are_not_guessed() -> None:
    other = SeriesRequest("oecd", "DSD_KEI@DF_KEI", "USA.M.X", "US", "monthly", "index")
    with pytest.raises(ConnectorError, match="dataflow"):
        oecd.fetch(_fetcher(lambda r: httpx.Response(200, text="")), other)
