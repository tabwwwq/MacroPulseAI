"""Credentials never survive into stored URLs or messages."""

from __future__ import annotations

import pytest

from macropulse_economics.redact import redact_secrets

KEY = "0123456789abcdef" * 2


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            f"https://api.stlouisfed.org/fred/series/observations?series_id=GDPC1&api_key={KEY}&file_type=json",
            "https://api.stlouisfed.org/fred/series/observations?series_id=GDPC1&api_key=REDACTED&file_type=json",
        ),
        (f"https://x.example/a?token={KEY}", "https://x.example/a?token=REDACTED"),
        (
            "postgresql+psycopg://user:hunter2@db:5432/x",
            "postgresql+psycopg://user:REDACTED@db:5432/x",
        ),
        (f"request failed: apikey={KEY} (HTTP 403)", "request failed: apikey=REDACTED (HTTP 403)"),
        (
            "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPC1",
            "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPC1",
        ),
        (
            "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/namq_10_gdp?geo=DE&unit=CLV20_MNAC",
            "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/namq_10_gdp?geo=DE&unit=CLV20_MNAC",
        ),
    ],
)
def test_redacts_credentials_and_keeps_everything_else(raw: str, expected: str) -> None:
    assert redact_secrets(raw) == expected


def test_none_passes_through() -> None:
    assert redact_secrets(None) is None
