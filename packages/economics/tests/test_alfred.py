"""ALFRED (FRED real-time) client: parsing, pagination, key handling. No network."""

from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from macropulse_economics.connectors import ConnectorError, SeriesRequest
from macropulse_economics.connectors.alfred import (
    ALFRED_OBSERVATIONS,
    REALTIME_END,
    REALTIME_START,
    VintageObservation,
    fetch_vintages,
    parse_vintage_page,
)
from macropulse_economics.connectors.http import Fetcher, make_client

US_GDP = SeriesRequest("fred", "GDPC1", "GDPC1", "US", "quarterly", "Billions of chained dollars")
US_UNRATE = SeriesRequest("fred", "UNRATE", "UNRATE", "US", "monthly", "%")
KEY = "0123456789abcdef0123456789abcdef"  # fake test value


def page(rows: list[dict[str, str]], count: int | None = None, offset: int = 0) -> dict[str, Any]:
    return {
        "realtime_start": REALTIME_START,
        "realtime_end": REALTIME_END,
        "count": len(rows) if count is None else count,
        "offset": offset,
        "limit": 100000,
        "observations": rows,
    }


GDP_ROWS = [
    {
        "realtime_start": "2008-10-30",
        "realtime_end": "2008-11-25",
        "date": "2008-07-01",
        "value": "11712.4",
    },
    {
        "realtime_start": "2008-11-26",
        "realtime_end": "9999-12-31",
        "date": "2008-07-01",
        "value": "11706.1",
    },
    {
        "realtime_start": "1996-01-19",
        "realtime_end": "1997-05-06",
        "date": "1947-01-01",
        "value": ".",
    },
]


def fetcher_for(handler: Any) -> Fetcher:
    return Fetcher(make_client(httpx.MockTransport(handler)), sleep=lambda _s: None)


class TestParse:
    def test_rows_become_vintage_observations_with_our_period_labels(self) -> None:
        rows, count = parse_vintage_page(page(GDP_ROWS), US_GDP)
        assert count == 3
        assert rows[0] == VintageObservation(
            "2008-Q3", 11712.4, date(2008, 10, 30), date(2008, 11, 25)
        )

    def test_open_ended_vintage_has_no_end_date(self) -> None:
        rows, _ = parse_vintage_page(page(GDP_ROWS), US_GDP)
        assert rows[1].realtime_end is None
        assert rows[1].value == 11706.1

    def test_missing_marker_is_kept_as_none_not_dropped(self) -> None:
        # "." means the value was not available in that vintage — information, not noise.
        rows, _ = parse_vintage_page(page(GDP_ROWS), US_GDP)
        assert rows[2] == VintageObservation("1947-Q1", None, date(1996, 1, 19), date(1997, 5, 6))

    def test_monthly_series_use_month_labels(self) -> None:
        rows, _ = parse_vintage_page(
            page(
                [
                    {
                        "realtime_start": "2020-05-08",
                        "realtime_end": "9999-12-31",
                        "date": "2020-04-01",
                        "value": "14.7",
                    }
                ]
            ),
            US_UNRATE,
        )
        assert rows[0].period == "2020-04"

    @pytest.mark.parametrize(
        "broken",
        [
            {"count": 1},  # no observations list
            page(
                [
                    {
                        "realtime_start": "2008-10-30",
                        "realtime_end": "9999-12-31",
                        "date": "2008-08-01",
                        "value": "1",
                    }
                ]
            ),
            page(
                [
                    {
                        "realtime_start": "2008-10-30",
                        "realtime_end": "9999-12-31",
                        "date": "2008-07-01",
                        "value": "n/a",
                    }
                ]
            ),
            page(
                [
                    {
                        "realtime_start": "2008-11-30",
                        "realtime_end": "2008-10-30",
                        "date": "2008-07-01",
                        "value": "1",
                    }
                ]
            ),
            page(
                [{"realtime_start": "2008-10-30", "date": "2008-07-01", "value": "1"}]
            ),  # no realtime_end
        ],
        ids=[
            "no-observations",
            "not-a-quarter-start",
            "bad-value",
            "end-before-start",
            "missing-field",
        ],
    )
    def test_malformed_responses_are_rejected(self, broken: dict[str, Any]) -> None:
        with pytest.raises(ConnectorError, match="GDPC1"):
            parse_vintage_page(broken, US_GDP)


class TestFetch:
    def test_requests_every_vintage_as_json_with_the_key(self) -> None:
        seen: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return httpx.Response(200, json=page(GDP_ROWS))

        result = fetch_vintages(fetcher_for(handler), US_GDP, KEY)
        assert len(seen) == 1
        url = urlsplit(str(seen[0].url))
        assert f"{url.scheme}://{url.netloc}{url.path}" == ALFRED_OBSERVATIONS
        params = {k: v[0] for k, v in parse_qs(url.query).items()}
        assert params["series_id"] == "GDPC1"
        assert params["api_key"] == KEY
        assert params["file_type"] == "json"
        assert params["realtime_start"] == REALTIME_START == "1776-07-04"
        assert params["realtime_end"] == REALTIME_END == "9999-12-31"
        assert params["offset"] == "0"
        assert len(result.observations) == 3
        assert result.request is US_GDP

    def test_pages_until_count_is_reached(self) -> None:
        offsets: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            offset = int(request.url.params["offset"])
            offsets.append(str(offset))
            return httpx.Response(
                200, json=page(GDP_ROWS[offset : offset + 2], count=3, offset=offset)
            )

        result = fetch_vintages(fetcher_for(handler), US_GDP, KEY, page_size=2)
        assert offsets == ["0", "2"]
        assert [o.period for o in result.observations] == ["2008-Q3", "2008-Q3", "1947-Q1"]

    def test_an_empty_page_before_count_is_an_error_not_an_endless_loop(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=page([], count=5))

        with pytest.raises(ConnectorError, match="GDPC1"):
            fetch_vintages(fetcher_for(handler), US_GDP, KEY)

    def test_the_stored_url_never_contains_the_key(self) -> None:
        result = fetch_vintages(
            fetcher_for(lambda r: httpx.Response(200, json=page(GDP_ROWS))), US_GDP, KEY
        )
        assert KEY not in result.url
        assert "api_key=REDACTED" in result.url
        assert result.url.startswith(ALFRED_OBSERVATIONS)

    def test_a_rejected_key_is_reported_without_echoing_it(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                400,
                json={
                    "error_code": 400,
                    "error_message": f"Bad Request. api_key {KEY} is not registered.",
                },
            )

        with pytest.raises(ConnectorError) as info:
            fetch_vintages(fetcher_for(handler), US_GDP, KEY)
        assert KEY not in str(info.value)

    @pytest.mark.parametrize("key", [None, "", "   "])
    def test_no_key_means_no_request(self, key: str | None) -> None:
        def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - must not run
            raise AssertionError("no request may be sent without a key")

        with pytest.raises(ConnectorError, match="FRED_API_KEY"):
            fetch_vintages(fetcher_for(handler), US_GDP, key)

    def test_only_fred_series_are_accepted(self) -> None:
        other = SeriesRequest("eurostat", "namq_10_gdp", "x", "DE", "quarterly", "x")
        with pytest.raises(ConnectorError, match="FRED"):
            fetch_vintages(fetcher_for(lambda r: httpx.Response(200, json=page([]))), other, KEY)

    def test_a_server_that_caps_the_page_size_loses_no_rows(self) -> None:
        # The client asks for 1000 rows; the server returns at most 2 per page.
        def handler(request: httpx.Request) -> httpx.Response:
            offset = int(request.url.params["offset"])
            return httpx.Response(200, json=page(GDP_ROWS[offset : offset + 2], count=3))

        result = fetch_vintages(fetcher_for(handler), US_GDP, KEY, page_size=1000)
        assert len(result.observations) == 3


def test_non_string_fields_are_a_connector_error() -> None:
    bad = page(
        [
            {
                "realtime_start": 20081030,
                "realtime_end": REALTIME_END,
                "date": "2008-07-01",
                "value": "1",
            }
        ]
    )
    with pytest.raises(ConnectorError, match="GDPC1"):
        parse_vintage_page(bad, US_GDP)
