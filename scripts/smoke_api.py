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
from datetime import date, timedelta
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

    def post_json(
        self, path: str, payload: Any, allowed: set[int] | None = None
    ) -> tuple[int, Any]:
        req = urllib.request.Request(  # noqa: S310 - scheme validated in __init__
            self.base + path,
            data=json.dumps(payload).encode(),
            headers={"User-Agent": "macropulse-smoke", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
                status, body = r.status, r.read()
        except urllib.error.HTTPError as e:
            status, body = e.code, e.read()
        self.check(status in {200} | (allowed or set()), f"POST {path}: HTTP {status}")
        try:
            return status, json.loads(body)
        except ValueError:
            self.check(False, f"POST {path}: body is not JSON")
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


def check_models(s: Smoke, countries: list[str]) -> None:
    """Inference round trip for every country and horizon, plus history and curves. Skipped (and
    reported) when no model is trained — a 503 with a training hint is the expected answer then."""
    status, models = s.json("/api/models")
    if not models or not models.get("items"):
        status, body = s.json("/api/recession/predict?country=DE&horizon=2", {503})
        s.check(status == 503 and body["error"]["code"] == "model_not_trained", "untrained not 503")
        print("models: none trained (predict correctly answers 503)")
        return
    for iso in countries:
        for h in (2, 4):
            status, e = s.json(f"/api/recession/predict?country={iso}&horizon={h}", {404})
            if status != 200:
                continue
            p = e["probability"]
            s.check(0 <= p <= 1, f"{iso}/H{h}: probability out of range")
            s.check(bool(e["model"]["id"]) and bool(e["as_of"]), f"{iso}/H{h}: no model/as-of")
            if e["stored_estimate"] is not None:
                s.check(abs(e["stored_estimate"] - p) < 1e-9, f"{iso}/H{h}: round trip mismatch")
            s.check(len(e["explanation"]["items"]) > 0, f"{iso}/H{h}: no explanation")
            status, hist = s.json(f"/api/recession/history?country={iso}&horizon={h}")
            s.check(
                bool(hist)
                and all(pt["split"] != "live" or pt["label"] is None for pt in hist["points"]),
                f"{iso}/H{h}: history live point carries a label",
            )
    for m in models["items"]:
        if m["status"] == "evaluated" and m["selected"]:
            _, curves = s.json(f"/api/models/{m['id']}/curves")
            for c in curves["splits"]:
                s.check(c["roc"] is not None or bool(c["note"]), f"{m['id']}: curve without note")
    status, body = s.json("/api/recession/predict?country=DE&horizon=3", {422})
    s.check(status == 422 and body["error"]["code"] == "unsupported_horizon", "H=3 not rejected")
    print(f"models: run {models['run_id']}, {len(models['items'])} versions, inference checked")


def check_forecasts(s: Smoke, countries: list[str]) -> None:
    """Every country x forecast metric at one horizon, plus a past as-of: paths start after the
    origin, intervals contain the point, nothing after the cut-off is used as input."""
    served = 0
    for iso in countries:
        for metric in sorted(CORE):
            status, fc = s.json(
                f"/api/forecasts?country={iso}&metric={metric}&horizon=4", {404, 503}
            )
            if status != 200:
                continue
            served += 1
            tag = f"forecast {iso}/{metric}"
            s.check(fc["actuals"][-1]["period"] == fc["origin"], f"{tag}: actuals pass origin")
            s.check(fc["realised"] == [], f"{tag}: latest forecast has realised values")
            for m in fc["models"]:
                s.check(len(m["path"]) == fc["steps"] or not m["available"], f"{tag}: path length")
                for pt in m["path"]:
                    s.check(pt["period"] > fc["origin"], f"{tag}: path before origin")
                    s.check(finite(pt["value"]), f"{tag}: non-finite forecast")
                    if pt["lower"] is not None:
                        s.check(pt["lower"] <= pt["value"] <= pt["upper"], f"{tag}: bad interval")
            for row in fc["backtest"]["metrics"]:
                cov = row["coverage"]
                s.check(cov is None or 0 <= cov <= 1, f"{tag}: coverage out of range")
    s.check(served > 0, "no forecast served for any country")
    status, past = s.json("/api/forecasts?country=US&metric=real_gdp_qoq&horizon=4&as_of=2008-Q2")
    if status == 200:
        s.check(past["origin"] <= "2008-Q2", "past as-of forecast uses later data")
        s.check(len(past["realised"]) == 4, "past as-of lacks realised values")
    status, body = s.json("/api/forecasts?country=DE&metric=real_gdp_qoq&horizon=3", {422})
    s.check(
        status == 422 and body["error"]["code"] == "unsupported_horizon", "forecast H=3 accepted"
    )
    print(f"forecasts: {served} country/metric series served")


def check_scenarios(s: Smoke, countries: list[str]) -> None:
    """Zero shock reproduces the live estimate; bounded shocks move only their mapped inputs."""
    _, spec = s.json("/api/scenarios/spec")
    s.check(bool(spec) and "not a causal" in spec["disclaimer"], "scenario disclaimer missing")
    evaluated = 0
    for iso in countries:
        for h in (2, 4):
            status, est = s.json(f"/api/recession/predict?country={iso}&horizon={h}", {404, 503})
            if status != 200:
                continue
            body = {"country": iso, "horizon": h}
            _, base = s.post_json("/api/scenarios/evaluate", body)
            s.check(
                abs(base["baseline"]["probability"] - est["probability"]) < 1e-9,
                f"scenario {iso}/H{h}: baseline differs from live estimate",
            )
            s.check(base["delta"] == 0, f"scenario {iso}/H{h}: zero shock moved the estimate")
            _, shocked = s.post_json(
                "/api/scenarios/evaluate", body | {"shocks": {"policy_rate": 1.0}}
            )
            changed = {i["feature"] for i in shocked["inputs"] if i["changed"]}
            s.check(
                changed <= {"rate", "rate_chg_4q", "term_spread"},
                f"scenario {iso}/H{h}: unexpected inputs moved {changed}",
            )
            s.check(0 <= shocked["scenario"]["probability"] <= 1, f"scenario {iso}/H{h}: range")
            evaluated += 1
    status, _ = s.post_json(
        "/api/scenarios/evaluate", {"country": "DE", "horizon": 4, "shocks": {"gdp": 50}}, {422}
    )
    s.check(status == 422, "out-of-bounds shock accepted")
    print(f"scenarios: {evaluated} country/horizon pairs evaluated")


def _end(period: str) -> date:
    y, rest = int(period[:4]), period[5:]
    if rest.startswith("Q"):
        m = int(rest[1]) * 3
    elif len(rest) == 2:
        m = int(rest)
    else:
        return date.fromisoformat(period)
    nxt = date(y + (m == 12), m % 12 + 1, 1)
    return nxt - timedelta(days=1)


def check_replay(s: Smoke, countries: list[str]) -> None:
    """Replays equal the walk-forward history, inputs respect their lags, outcomes come later."""
    _, presets = s.json("/api/history/presets")
    replayed = 0
    for iso in countries:
        for h in (2, 4):
            status, eps = s.json(f"/api/history/episodes?country={iso}&horizon={h}", {404, 503})
            if status != 200:
                continue
            c = eps["confusion"]
            s.check(all(v >= 0 for v in c.values()), f"episodes {iso}/H{h}: negative count")
            _, hist = s.json(f"/api/recession/history?country={iso}&horizon={h}")
            wf = {p["as_of"]: p["probability"] for p in hist["points"] if p["split"] != "live"}
            for pre in presets:
                q = pre["as_of"]
                st, r = s.json(f"/api/history/replay?country={iso}&horizon={h}&as_of={q}", {404})
                if st != 200:
                    s.check(r["error"]["code"] == "replay_unavailable", f"replay {iso}/{q}: code")
                    continue
                replayed += 1
                tag = f"replay {iso}/H{h}/{q}"
                s.check(
                    abs(r["probability"] - wf.get(q, -1)) < 1e-9,
                    f"{tag}: not the walk-forward value",
                )
                s.check("approximation" in r["basis"]["label"], f"{tag}: basis label missing")
                cutoff = date.fromisoformat(r["cutoff"])
                for i in r["inputs"]:
                    ok = _end(i["period"]) + timedelta(days=i["publication_lag_days"]) <= cutoff
                    s.check(ok, f"{tag}: {i['feature']} not published by the cut-off")
                s.check(
                    all(w > q for w in r["outcome"]["window"]), f"{tag}: window not after as-of"
                )
                s.check(int(r["model"]["trained_through_as_of"][:4]) < int(q[:4]), f"{tag}: fold")
                s.check((r["nber"] is not None) == (iso == "US"), f"{tag}: NBER reference scope")
    status, body = s.json("/api/history/replay?country=DE&horizon=3&as_of=2008-Q2", {422})
    s.check(status == 422 and body["error"]["code"] == "unsupported_horizon", "replay H=3 accepted")
    print(f"replay: {replayed} crisis replays checked")


def run(base: str) -> Smoke:
    s = Smoke(base)
    _, health = s.json("/api/health")
    s.check(bool(health) and health.get("status") == "ok", "health is not ok")
    _, catalog = s.json("/api/indicators/catalog")
    _, countries = s.json("/api/countries")
    for country in countries["items"]:
        check_country(s, country, catalog)
    check_lineage(s)
    isos = [c["iso2"] for c in countries["items"]]
    check_models(s, isos)
    check_forecasts(s, isos)
    check_scenarios(s, isos)
    check_replay(s, isos)
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
