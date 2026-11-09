"""End-to-end smoke test of a running MacroPulse API over its real stored data (stdlib only).

Walks every country, KPI, indicator and stored series the API exposes and checks invariants that
must hold for real data: no 5xx, every shown value has provenance, support levels match what is
stored, CSV exports match the stored row counts, and absent data is reported (404/503), never
filled. Exit code 0 only when every check passes.

    uv run python scripts/smoke_api.py --base-url http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

EXPECTED_ABSENCE = {404, 503}
CORE = {"real_gdp_qoq", "inflation_yoy", "unemployment_rate"}


class Smoke:
    def __init__(self, base: str) -> None:
        if urllib.parse.urlsplit(base).scheme not in {"http", "https"}:
            raise ValueError("--base-url must be an http(s) URL")
        self.base = base.rstrip("/")
        self.failures: list[str] = []
        self.checks = 0

    def get(self, path: str) -> tuple[int, bytes, dict[str, str]]:
        url = self.base + path  # scheme validated in __init__
        req = urllib.request.Request(url, headers={"User-Agent": "macropulse-smoke"})  # noqa: S310
        try:
            with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, e.read(), dict(e.headers)

    def json(self, path: str, allowed: set[int] | None = None) -> tuple[int, Any]:
        status, body, _ = self.get(path)
        self.check(status in {200} | (allowed or set()), f"{path}: HTTP {status}")
        try:
            return status, json.loads(body)
        except ValueError:
            self.check(False, f"{path}: body is not JSON")
            return status, None

    def check(self, condition: bool, message: str) -> None:
        self.checks += 1
        if not condition:
            self.failures.append(message)


def finite(x: Any) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x)


def check_kpis(s: Smoke, iso: str) -> None:
    """KPI values carry provenance; absent values carry a reason and no number."""
    _, summary = s.json(f"/api/countries/{iso}/summary")
    for k in summary["kpis"]:
        ind = k["indicator"]["id"]
        if k["status"] == "ok":
            prov = k["provenance"] or {}
            s.check(finite(k["value"]), f"{iso}/{ind}: non-finite KPI value")
            s.check(bool(k["period"]), f"{iso}/{ind}: KPI without period")
            s.check(bool(prov.get("request_url")), f"{iso}/{ind}: KPI without request URL")
            s.check(bool(prov.get("retrieved_at")), f"{iso}/{ind}: KPI without retrieval time")
        else:
            s.check(k["value"] is None, f"{iso}/{ind}: value shown with status {k['status']}")
            s.check(bool(k["reason"]), f"{iso}/{ind}: missing value without a reason")


def check_indicators(s: Smoke, iso: str, entries: list[dict[str, Any]]) -> set[str]:
    """Every catalog indicator answers 200 with provenance or an explicit 404/503, never a 5xx."""
    stored_core: set[str] = set()
    for e in entries:
        ind = e["indicator"]["id"]
        q = urllib.parse.urlencode({"country": iso, "indicator": ind})
        status, body = s.json(f"/api/indicators?{q}", EXPECTED_ABSENCE)
        if status != 200:
            s.check(body is not None and "error" in body, f"{iso}/{ind}: absence without error")
            continue
        periods = [p["period"] for p in body["points"]]
        s.check(all(finite(p["value"]) for p in body["points"]), f"{iso}/{ind}: non-finite point")
        s.check(len(periods) == len(set(periods)), f"{iso}/{ind}: duplicate periods")
        s.check(
            body["provenance"]["native_observations"] == e["ingestion"]["observations"],
            f"{iso}/{ind}: catalog count != stored rows",
        )
        if ind in CORE and periods:
            stored_core.add(ind)
    return stored_core


def check_country(s: Smoke, country: dict[str, Any], catalog: dict[str, Any]) -> None:
    iso = country["iso2"]
    support = country["support"]["level"]
    check_kpis(s, iso)
    entries = next(c for c in catalog["countries"] if c["country"] == iso)["items"]
    stored_core = check_indicators(s, iso, entries)
    if support == "full":
        s.check(stored_core == CORE, f"{iso}: full support but stored core = {sorted(stored_core)}")
    if support == "unavailable":
        s.check("real_gdp_qoq" not in stored_core, f"{iso}: unavailable but GDP stored")
    print(f"{iso}: support={support:<11} stored core={sorted(stored_core)}")


def check_lineage(s: Smoke) -> None:
    """CSV exports hold exactly the stored rows, with provenance on each row."""
    _, inventory = s.json("/api/data-quality")
    for item in inventory["items"]:
        if item["observations"] == 0:
            continue
        sid = item["series_id"]
        status, body, headers = s.get(item["export_path"])
        s.check(status == 200, f"{sid}: CSV HTTP {status}")
        if status != 200:
            continue
        s.check(headers.get("content-type", "").startswith("text/csv"), f"{sid}: not CSV")
        rows = list(csv.DictReader(io.StringIO(body.decode("utf-8"))))
        s.check(len(rows) == item["observations"], f"{sid}: CSV rows != stored rows")
        s.check(
            all(r["source_url"] and r["retrieved_at"] for r in rows), f"{sid}: row lacks provenance"
        )
    total = sum(i["observations"] for i in inventory["items"])
    print(
        f"inventory: {len(inventory['items'])} series, {total} observations, {inventory['counts']}"
    )


def run(base: str) -> Smoke:
    s = Smoke(base)
    _, health = s.json("/api/health")
    s.check(bool(health) and health.get("status") == "ok", "health is not ok")
    _, catalog = s.json("/api/indicators/catalog")
    _, countries = s.json("/api/countries")
    for country in countries["items"]:
        check_country(s, country, catalog)
    check_lineage(s)
    status, body = s.json("/api/countries/XX/summary", {422})
    s.check(status == 422 and body["error"]["code"] == "unsupported_country", "XX not rejected")
    status, _ = s.json("/api/countries/DE/summary?as_of=2999-Q1", {422})
    s.check(status == 422, "future as_of not rejected")
    return s


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test a running MacroPulse API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    try:
        smoke = run(args.base_url)
    except urllib.error.URLError as exc:
        print(f"API not reachable at {args.base_url}: {exc.reason}", file=sys.stderr)
        return 2
    for f in smoke.failures:
        print(f"FAIL {f}")
    print(f"{smoke.checks - len(smoke.failures)}/{smoke.checks} checks passed")
    return 0 if not smoke.failures else 1


if __name__ == "__main__":
    sys.exit(main())
