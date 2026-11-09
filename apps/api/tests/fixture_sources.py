"""Offline stand-in for the official sources, built from real captured responses.

`fixture_fetch` serves packages/economics/tests/fixtures (DE real GDP levels, FR HICP, the ECB
deposit-facility rate) and fails every other series, exactly as an unreachable source would.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
from fastapi import FastAPI

from macropulse_api.services.sync import SyncReport, run_sync
from macropulse_economics.connectors import (
    ConnectorError,
    FetchResult,
    SeriesRequest,
    ecb,
    eurostat,
)
from macropulse_economics.connectors.http import Fetcher, make_client

FIXTURES = Path(__file__).resolve().parents[3] / "packages" / "economics" / "tests" / "fixtures"
TODAY = date(2026, 11, 9)
DE_GDP_ID = "eurostat:namq_10_gdp:freq=Q, unit=CLV20_MNAC, s_adj=SCA, na_item=B1GQ:DE"


def fixture_fetch(_fetcher: Fetcher, req: SeriesRequest) -> FetchResult:
    now = datetime.now(UTC)
    if (req.dataset, req.geo) == ("namq_10_gdp", "DE"):
        payload = json.loads((FIXTURES / "eurostat_namq_10_gdp_DE_last6.json").read_text("utf-8"))
        obs, unit, updated = eurostat.parse_jsonstat(payload, req)
        return FetchResult(req, obs, "https://ec.europa.eu/x?geo=DE", now, updated, unit)
    if (req.dataset, req.geo) == ("prc_hicp_minr", "FR"):
        payload = json.loads((FIXTURES / "eurostat_prc_hicp_minr_FR_last4.json").read_text("utf-8"))
        obs, unit, updated = eurostat.parse_jsonstat(payload, req)
        return FetchResult(req, obs, "https://ec.europa.eu/y?geo=FR", now, updated, unit)
    if req.source_id == "ecb":
        obs, unit = ecb.parse_csv((FIXTURES / "ecb_FM_DFR_last4.csv").read_text("utf-8"), req)
        return FetchResult(req, obs, "https://data-api.ecb.europa.eu/z", now, unit_label=unit)
    raise ConnectorError(f"{req.dataset}: not captured (offline test)")


def offline_fetcher() -> Fetcher:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise AssertionError("tests must not touch the network")

    return Fetcher(make_client(transport=httpx.MockTransport(refuse)), sleep=lambda _s: None)


def sync_fixtures(app: FastAPI, fetcher: Fetcher, **kwargs: object) -> SyncReport:
    params: dict[str, object] = {
        "sources": ["eurostat", "ecb"],
        "countries": ["DE", "FR"],
        "today": TODAY,
        "fetch": fixture_fetch,
    }
    params.update(kwargs)
    return run_sync(app.state.sessionmaker, fetcher, **params)  # type: ignore[arg-type]
