"""Opt-in checks against the real official APIs (MACROPULSE_LIVE_TESTS=1).

They verify that each verified mapping still returns a parseable single series with recent data.
Run: `$env:MACROPULSE_LIVE_TESTS = "1"; uv run pytest -m live`
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from macropulse_economics.connectors import SeriesRequest, fetch_series
from macropulse_economics.connectors.http import Fetcher, make_client
from macropulse_economics.quality import run_checks
from macropulse_economics.series import native_series

pytestmark = pytest.mark.live

REQUESTS, _ = native_series(["DE", "US"])


@pytest.fixture(scope="module")
def fetcher() -> Iterator[Fetcher]:
    with make_client() as client:
        yield Fetcher(client)


@pytest.mark.parametrize("req", REQUESTS, ids=lambda r: r.series_id)
def test_live_series_parses_and_passes_hard_quality_rules(
    fetcher: Fetcher, req: SeriesRequest
) -> None:
    result = fetch_series(fetcher, req)
    assert result.observations, req.series_id
    failing = [c for c in run_checks(result, datetime.now(UTC).date()) if c.status == "fail"]
    assert not failing, failing
