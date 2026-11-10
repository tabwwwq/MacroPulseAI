"""Offline stand-in for the official sources, built from real captured responses.

`fixture_fetch` serves packages/economics/tests/fixtures (DE real GDP levels, FR HICP, the ECB
deposit-facility rate) and fails every other series, exactly as an unreachable source would.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
import numpy as np
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
from macropulse_economics.periods import shift
from macropulse_ml.features import CountryInputs

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


def synthetic_country_inputs(country: str, seed: int) -> CountryInputs:
    rng = np.random.default_rng(seed)
    quarters = [f"{y}-Q{q}" for y in range(1985, 2027) for q in (1, 2, 3, 4)][
        : (2026 - 1985) * 4 + 3
    ]
    growth = 0.5 + 0.3 * rng.standard_normal(len(quarters))
    stress = np.zeros(len(quarters))
    for start in range(10, len(quarters) - 3, 22):
        growth[start : start + 2] = [-0.6, -0.4]
        stress[start - 4 : start + 2] = np.linspace(0.2, 1.4, 6)
    gdp_qoq = {p: float(g) for p, g in zip(quarters, growth, strict=True)}
    level = np.cumprod(1 + growth / 100)
    gdp_yoy = {
        quarters[i]: float((level[i] / level[i - 4] - 1) * 100) for i in range(4, len(quarters))
    }
    months: list[str] = []
    m = "1985-01"
    while m != "2026-10":
        months.append(m)
        m = shift(m, 1)
    s = np.repeat(stress, 3)[: len(months)]
    noise = rng.standard_normal(len(months))
    return CountryInputs(
        country=country,
        gdp_qoq=gdp_qoq,
        gdp_yoy=gdp_yoy,
        inflation={mm: 2 + 0.3 * n for mm, n in zip(months, noise, strict=True)},
        unemployment={mm: 6 + v for mm, v in zip(months, s, strict=True)},
        policy_rate={mm: 3 - v for mm, v in zip(months, s, strict=True)},
        policy_rate_event_dated=False,
        bond_yield={mm: 4.5 - 2 * v for mm, v in zip(months, s, strict=True)},
        short_rate={mm: 3 - v for mm, v in zip(months, s, strict=True)},
    )
