"""Credential-free source feasibility probe (Python 3.12, standard library only).

Coverage counts refer to nonmissing observations in the requested slice, not to
an assertion about uninterrupted coverage. Never substitutes guessed SDMX keys.
"""

import argparse
import csv
import io
import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

COUNTRIES = ("BE", "DE", "FR", "NL", "US", "EA")
EU = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
UA = "MacroPulse-feasibility-probe/0.1"

try:  # Optional Mozilla CA bundle: Python on Windows does not fetch on-demand roots (e.g. EU sites).
    import certifi

    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
    CA_SOURCE = "certifi"
except ImportError:
    SSL_CONTEXT = ssl.create_default_context()
    CA_SOURCE = "system"


def utc() -> str:
    return datetime.now(UTC).isoformat()


class Probe:
    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.records: list[dict[str, Any]] = []

    def get(self, url: str, accept: str = "*/*") -> tuple[bytes | None, dict[str, Any]]:
        evidence: dict[str, Any] = {
            "request_url": url,
            "retrieved_at_utc": utc(),
            "http_status": None,
            "attempts": [],
        }
        body = None
        for attempt in range(3):
            if attempt:
                time.sleep(2 ** (attempt - 1))
            try:
                request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
                with urllib.request.urlopen(request, timeout=20, context=SSL_CONTEXT) as response:
                    body = response.read()
                    evidence.update(
                        http_status=response.status,
                        final_url=response.url,
                        content_type=response.headers.get("Content-Type"),
                    )
                evidence["attempts"].append({"at": utc(), "http_status": evidence["http_status"]})
                break
            except (OSError, urllib.error.URLError) as exc:
                status = getattr(exc, "code", None)
                evidence["http_status"] = status
                evidence["attempts"].append(
                    {"at": utc(), "http_status": status, "error": f"{type(exc).__name__}: {exc}"}
                )
        evidence["retrieved_at_utc"] = utc()
        self.requests.append(evidence)
        time.sleep(0.25)
        return body, evidence

    def record(
        self,
        country: str,
        indicator: str,
        source: str,
        code: str | None,
        evidence: dict[str, Any],
        **fields: Any,
    ) -> None:
        row = dict(
            country=country,
            indicator=indicator,
            source=source,
            dataset_or_series_code=code,
            exact_filter_or_key=None,
            frequency=None,
            unit=None,
            seasonal_adjustment=None,
            first_period=None,
            last_period=None,
            observation_count=None,
            http_status=evidence.get("http_status"),
            retrieved_at_utc=evidence.get("retrieved_at_utc"),
            request_url=evidence.get("request_url"),
            status="unverified",
            notes=[],
        )
        row.update(fields)
        self.records.append(row)

    def eurostat(self) -> None:
        # Discover current dataset identifiers from the official catalogue.
        body, catalogue = self.get(
            "https://ec.europa.eu/eurostat/api/dissemination/catalogue/toc/xml?lang=EN"
        )
        datasets: dict[str, str] = {}
        if body:
            try:
                root = ET.fromstring(body)
                for element in root.iter():
                    code = element.attrib.get("code")
                    if code:
                        datasets[code] = " ".join(element.itertext()).strip()
            except ET.ParseError as exc:
                catalogue["parse_error"] = str(exc)
        specs = {
            "real_gdp": ("gross domestic product", "quarter"),
            "unemployment": ("unemployment", "monthly"),
            "inflation": ("hicp", "annual rate of change"),
            "quarterly_debt": ("government", "debt", "quarter"),
        }
        for indicator, words in specs.items():
            candidates = [
                code
                for code, title in datasets.items()
                if all(word in title.lower() for word in words)
            ]
            # The brief supplies two starting identifiers; validate via response dimensions.
            seed = {"real_gdp": "namq_10_gdp", "quarterly_debt": "gov_10q_ggdebt"}.get(indicator)
            if seed:
                candidates = [seed] + [c for c in candidates if c != seed]
            if not candidates:
                for country in COUNTRIES:
                    self.record(
                        country,
                        indicator,
                        "Eurostat",
                        None,
                        catalogue,
                        notes=["Dataset discovery unavailable or no unambiguous catalogue match."],
                    )
                continue
            discovered = False
            for code in candidates[:12]:
                raw, meta = self.get(EU + code + "?lastTimePeriod=1&lang=EN")
                if not raw:
                    continue
                try:
                    dataset = json.loads(raw)
                    dimensions = dataset["dimension"]
                    filters: dict[str, str] = {}
                    for name, dimension in dimensions.items():
                        if name in ("geo", "time"):
                            continue
                        labels = dimension["category"]["label"]
                        chosen = self.choose_dimension(name, labels, indicator)
                        if chosen is None:
                            raise ValueError(f"Cannot select dimension {name} from official labels")
                        filters[name] = chosen
                    if indicator == "real_gdp" and filters.get("na_item") != "B1GQ":
                        raise ValueError("GDP B1GQ not discovered")
                except (ValueError, KeyError, TypeError) as exc:
                    meta["discovery_error"] = str(exc)
                    continue
                discovered = True
                for country in COUNTRIES:
                    geos = dimensions["geo"]["category"]["label"]
                    geo = country
                    if country == "EA":
                        # Select only an explicitly labelled aggregate, never compose one.
                        matches = [k for k, v in geos.items() if "euro area" in v.lower()]
                        geo = matches[0] if len(matches) == 1 else ""
                    if not geo:
                        self.record(
                            country,
                            indicator,
                            "Eurostat",
                            code,
                            meta,
                            notes=["EA aggregate not uniquely discovered in metadata slice."],
                        )
                        continue
                    query = dict(filters, geo=geo, lang="EN")
                    url = EU + code + "?" + urllib.parse.urlencode(query)
                    data, ev = self.get(url)
                    fields: dict[str, Any] = dict(
                        exact_filter_or_key=query,
                        frequency=filters.get("freq"),
                        unit=filters.get("unit"),
                        seasonal_adjustment=filters.get("s_adj"),
                    )
                    try:
                        obj = json.loads(data) if data else {}
                        if obj["id"][-1] != "time" or any(size != 1 for size in obj["size"][:-1]):
                            raise ValueError(
                                "Response is not a single series with time as final dimension"
                            )
                        times = obj["dimension"]["time"]["category"]["index"]
                        if isinstance(times, list):
                            times = {value: i for i, value in enumerate(times)}
                        values = obj.get("value", {})
                        if isinstance(values, list):
                            values = {str(i): v for i, v in enumerate(values) if v is not None}
                        periods = sorted(
                            t for t, i in times.items() if values.get(str(i)) is not None
                        )
                        if not periods:
                            raise ValueError("No nonmissing observations")
                        fields.update(
                            status="verified",
                            first_period=periods[0],
                            last_period=periods[-1],
                            observation_count=len(periods),
                            notes=[
                                "Latest revisions; full returned history; metadata request: "
                                + meta["request_url"]
                            ],
                        )
                    except (ValueError, KeyError, TypeError) as exc:
                        fields.update(status="failed", notes=[str(exc)])
                    self.record(country, indicator, "Eurostat", code, ev, **fields)
                break
            if not discovered:
                for country in COUNTRIES:
                    self.record(
                        country,
                        indicator,
                        "Eurostat",
                        None,
                        catalogue,
                        notes=["Metadata discovery failed; no data key guessed."],
                    )

    @staticmethod
    def choose_dimension(name: str, labels: dict[str, str], indicator: str) -> str | None:
        predicates = {
            "freq": lambda k, v: (
                ("quarter" if indicator in ("real_gdp", "quarterly_debt") else "month") in v
            ),
            "na_item": lambda k, v: k == "B1GQ",
            "s_adj": lambda k, v: (
                "seasonally and calendar adjusted" in v
                or "seasonally and working day adjusted" in v
            ),
            "unit": lambda k, v: (
                ("chain linked volumes" in v and "percentage" not in v and "million" in v)
                if indicator == "real_gdp"
                else (
                    "percentage of gross domestic product" in v
                    if indicator == "quarterly_debt"
                    else "percent" in v
                )
            ),
            "sex": lambda k, v: "total" in v,
            "age": lambda k, v: "15 to 74" in v,
            "coicop": lambda k, v: "all-items" in v or "all items" in v,
            "sector": lambda k, v: v == "general government",
            "s_adj_unused": lambda k, v: False,
        }
        if len(labels) == 1:
            return next(iter(labels))
        predicate = predicates.get(name)
        matches = [k for k, v in labels.items() if predicate and predicate(k, v.lower())]
        # Stable deterministic preference among explicitly matched real-volume reference years.
        return sorted(matches)[-1] if matches else None

    def fred(self) -> None:
        series = {
            "GDPC1": (
                "real_gdp",
                "quarterly",
                "billions of chained dollars",
                "seasonally adjusted annual rate",
            ),
            "UNRATE": ("unemployment", "monthly", "percent", "seasonally adjusted"),
            "CPIAUCSL": (
                "inflation",
                "monthly",
                "CPI index (not annual inflation)",
                "seasonally adjusted",
            ),
            "FEDFUNDS": ("policy_rate", "monthly", "percent", "not seasonally adjusted"),
            "T10Y3M": ("yield_spread", "daily", "percentage points", "not seasonally adjusted"),
            "USREC": ("nber_reference", "monthly", "0/1 indicator", "not seasonally adjusted"),
            "GFDEGDQ188S": (
                "federal_debt",
                "quarterly",
                "percent of GDP",
                "not seasonally adjusted",
            ),
        }
        for code, (indicator, frequency, unit, adjustment) in series.items():
            url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + code
            raw, ev = self.get(url)
            fields: dict[str, Any] = dict(
                exact_filter_or_key={"id": code},
                notes=[
                    "Requested identifier supplied by brief. Unit/frequency/adjustment require official metadata."
                ],
            )
            try:
                rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))) if raw else []
                valid = [row for row in rows if row.get(code) not in (None, "", ".")]
                for row in valid:
                    float(row[code])
                if not valid:
                    raise ValueError("No numeric observations returned")
                date_key = next(k for k in valid[0] if k != code)
                fields.update(
                    status="partial",
                    first_period=valid[0][date_key],
                    last_period=valid[-1][date_key],
                    observation_count=len(valid),
                    notes=[
                        "CSV values verified; frequency/unit/adjustment metadata unverified.",
                        "ALFRED vintages and release dates require FRED_API_KEY; not probed.",
                    ],
                )
            except (ValueError, UnicodeError, StopIteration) as exc:
                fields.update(status="failed", notes=[str(exc)])
            self.record("US", indicator, "FRED", code, ev, **fields)

    def world_bank(self) -> None:
        for code, indicator in (
            ("GC.DOD.TOTL.GD.ZS", "annual_central_debt"),
            ("NY.GDP.MKTP.KD.ZG", "annual_gdp_growth"),
        ):
            raw, metadata = self.get(f"https://api.worldbank.org/v2/indicator/{code}?format=json")
            try:
                definition = json.loads(raw)[1][0] if raw else None
                if not definition or definition["id"] != code:
                    raise ValueError("Indicator not confirmed")
            except (ValueError, KeyError, TypeError, IndexError):
                definition = None
            for country in COUNTRIES[:-1]:
                if not definition:
                    self.record(
                        country,
                        indicator,
                        "World Bank",
                        code,
                        metadata,
                        notes=["Official indicator metadata unavailable; data request withheld."],
                    )
                    continue
                url = f"https://api.worldbank.org/v2/country/{country}/indicator/{code}?format=json&per_page=1000"
                data, ev = self.get(url)
                fields: dict[str, Any] = dict(
                    exact_filter_or_key={"country": country, "indicator": code},
                    frequency="annual",
                    unit=definition.get("unit") or definition.get("name"),
                    seasonal_adjustment="not applicable (annual)",
                    notes=[definition.get("sourceNote", "")],
                )
                try:
                    obj = json.loads(data) if data else []
                    if obj[0]["pages"] != 1:
                        raise ValueError("Unexpected pagination; coverage not complete")
                    valid = sorted(r["date"] for r in obj[1] if r["value"] is not None)
                    missing = [r["date"] for r in obj[1] if r["value"] is None]
                    fields.update(
                        status="verified" if valid else "partial",
                        first_period=valid[0] if valid else None,
                        last_period=valid[-1] if valid else None,
                        observation_count=len(valid),
                        missing_periods=missing,
                        notes=[
                            "Annual only; central government scope differs from general government.",
                            "Metadata: " + metadata["request_url"],
                        ],
                    )
                except (ValueError, KeyError, TypeError, IndexError) as exc:
                    fields.update(status="failed", notes=[str(exc)])
                self.record(country, indicator, "World Bank", code, ev, **fields)

    def sdmx_discovery(self, source: str, url: str, indicators: tuple[str, ...]) -> None:
        raw, ev = self.get(url, "application/vnd.sdmx.structure+xml;version=2.1")
        flows = []
        if raw:
            try:
                root = ET.fromstring(raw)
                for node in root.iter():
                    if node.tag.rsplit("}", 1)[-1] == "Dataflow":
                        names = " ".join(
                            n.text or "" for n in node.iter() if n.tag.rsplit("}", 1)[-1] == "Name"
                        )
                        if (source == "ECB" and node.get("id") == "FM") or (
                            source == "OECD" and ("leading indicator" in names.lower())
                        ):
                            flows.append(
                                {
                                    "id": node.get("id"),
                                    "agency": node.get("agencyID"),
                                    "version": node.get("version"),
                                    "name": names,
                                }
                            )
            except ET.ParseError as exc:
                ev["parse_error"] = str(exc)
        ev["discovered_flows"] = flows
        if flows and source == "OECD":
            # Fetch a single CLI structure separately, avoiding ambiguous codelist IDs
            # across the all-dataflow response.
            flow = flows[0]
            structure_url = (
                "https://sdmx.oecd.org/public/rest/v1/dataflow/"
                f"{flow['agency']}/{flow['id']}/{flow['version']}?references=all"
            )
            raw, ev = self.get(structure_url, "application/vnd.sdmx.structure+xml;version=2.1")
        if raw and flows:
            try:
                root = ET.fromstring(raw)
                for indicator in indicators:
                    for country in ("EA",) if source == "ECB" else COUNTRIES[:-1]:
                        self.sdmx_slice(source, root, flows[0], country, indicator, ev)
                return
            except (ET.ParseError, ValueError, KeyError, TypeError) as exc:
                ev["discovery_error"] = str(exc)
        # Fail closed: discovering a flow is not sufficient evidence of a series key.
        for indicator in indicators:
            for country in ("EA",) if source == "ECB" else COUNTRIES[:-1]:
                self.record(
                    country,
                    indicator,
                    source,
                    None,
                    ev,
                    notes=[
                        "No validated dimension-level series key or data slice; unverified.",
                        "Shared euro area rate, not national rates."
                        if source == "ECB"
                        else "CLI flow discovery alone does not establish country coverage.",
                    ],
                )

    def sdmx_slice(
        self,
        source: str,
        root: ET.Element,
        flow: dict[str, Any],
        country: str,
        indicator: str,
        metadata: dict[str, Any],
    ) -> None:
        def local(node: ET.Element) -> str:
            return node.tag.rsplit("}", 1)[-1]

        lists: dict[str, dict[str, str]] = {}
        for node in root.iter():
            if local(node) == "Codelist":
                lists[node.attrib["id"]] = {
                    code.attrib["id"]: " ".join(
                        n.text or ""
                        for n in code
                        if local(n) == "Name"
                        and n.get("{http://www.w3.org/XML/1998/namespace}lang", "en") == "en"
                    )
                    for code in node
                    if local(code) == "Code"
                }
        descriptors = [n for n in root.iter() if local(n) == "DimensionList"]
        if len(descriptors) != 1:
            raise ValueError("Expected one unambiguous SDMX dimension descriptor")
        dimensions = sorted(
            (n for n in descriptors[0] if local(n) == "Dimension"),
            key=lambda n: int(n.get("position", "0")),
        )
        selections: dict[str, str] = {}
        country_names = {
            "BE": "belgium",
            "DE": "germany",
            "FR": "france",
            "NL": "netherlands",
            "US": "united states",
            "EA": "euro area",
        }
        for dimension in dimensions:
            name = dimension.attrib["id"]
            refs = [
                n for n in dimension.iter() if local(n) == "Ref" and n.get("class") == "Codelist"
            ]
            codes = lists.get(refs[0].get("id", ""), {}) if len(refs) == 1 else {}
            matches: list[str] = []
            for code, label in codes.items():
                label = label.lower()
                if name in ("REF_AREA", "REF_AREA_DSD", "COUNTRY"):
                    match = label == country_names[country] or (
                        country == "EA" and "euro area" in label
                    )
                elif name in ("FREQ", "FREQUENCY"):
                    match = "monthly" in label
                elif name == "CURRENCY":
                    match = label == "euro"
                elif name == "PROVIDER_FM":
                    match = "european central bank" in label
                elif name in ("INSTRUMENT_FM", "MEASURE"):
                    match = (
                        ("main refinancing" in label and "fixed" in label)
                        if indicator == "mro_rate"
                        else "deposit facility" in label
                        if indicator == "deposit_rate"
                        else "leading indicator" in label
                    )
                elif name == "FREQ_FM":
                    match = "end" in label and "period" in label
                elif name in ("ADJUSTMENT", "TRANSFORMATION", "METHODOLOGY", "UNIT_MEASURE"):
                    match = (
                        "amplitude adjusted" in label
                        or "long-term average = 100" in label
                        or label == "seasonally adjusted"
                    )
                else:
                    match = False
                if match:
                    matches.append(code)
            if len(codes) == 1:
                matches = list(codes)
            if len(matches) != 1:
                self.record(
                    country,
                    indicator,
                    source,
                    flow["id"],
                    metadata,
                    notes=[
                        f"Dimension {name}: {len(matches)} label matches; no key guessed.",
                        "Discovered selections: " + json.dumps(selections),
                    ],
                )
                return
            selections[name] = matches[0]
        key = ".".join(selections.values())
        base = (
            "https://data-api.ecb.europa.eu/service/data/FM/"
            if source == "ECB"
            else "https://sdmx.oecd.org/public/rest/v1/data/"
            f"{flow['agency']},{flow['id']},{flow['version']}/"
        )
        url = base + key + "?startPeriod=2020-01&format=csvfile"
        raw, ev = self.get(url, "text/csv")
        fields: dict[str, Any] = dict(
            exact_filter_or_key=key,
            dimension_filters=selections,
            frequency=selections.get("FREQ"),
            unit=selections.get("UNIT_MEASURE"),
            seasonal_adjustment=selections.get("ADJUSTMENT"),
            notes=[
                "Small slice since 2020; counts and first period refer only to that slice.",
                "Metadata: " + metadata["request_url"],
                "Shared euro area rate, not a national rate."
                if source == "ECB"
                else "CLI definitions require cross-country comparability review.",
            ],
        )
        try:
            rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))) if raw else []
            valid = [r for r in rows if r.get("OBS_VALUE") not in (None, "", ".")]
            for row in valid:
                float(row["OBS_VALUE"])
            periods = sorted(r["TIME_PERIOD"] for r in valid)
            if not periods:
                raise ValueError("No numeric SDMX CSV observations")
            fields.update(
                status="partial",
                first_period=periods[0],
                last_period=periods[-1],
                observation_count=len(periods),
            )
        except (ValueError, KeyError, UnicodeError) as exc:
            fields.update(status="failed", notes=fields["notes"] + [str(exc)])
        self.record(country, indicator, source, flow["id"], ev, **fields)

    # ------------------------------------------------------------------ explicit candidates
    # Candidate dataset codes / series keys taken from official documentation. A candidate counts as
    # verified only if the live response returns exactly one series with observations; the labels
    # reported come from the response itself, so the evidence shows what the key actually means.

    EUROSTAT_CANDIDATES: dict[str, tuple[str, dict[str, str]]] = {
        "unemployment": ("une_rt_m", {"s_adj": "SA", "age": "TOTAL", "sex": "T", "unit": "PC_ACT"}),
        "inflation": ("prc_hicp_manr", {"coicop": "CP00", "unit": "RCH_A"}),
        "quarterly_debt": ("gov_10q_ggdebt", {"unit": "PC_GDP", "sector": "S13", "na_item": "GD"}),
    }
    EUROSTAT_GEO = {"BE": "BE", "DE": "DE", "FR": "FR", "NL": "NL", "EA": "EA20"}

    def eurostat_explicit(self) -> None:
        for indicator, (code, filters) in self.EUROSTAT_CANDIDATES.items():
            # Replace the heuristic rows for this indicator with explicit-candidate evidence.
            self.records = [
                r
                for r in self.records
                if not (r["source"] == "Eurostat" and r["indicator"] == indicator)
            ]
            for country, geo in self.EUROSTAT_GEO.items():
                query = dict(filters, geo=geo, lang="EN")
                raw, ev = self.get(EU + code + "?" + urllib.parse.urlencode(query))
                fields: dict[str, Any] = dict(exact_filter_or_key=query)
                try:
                    obj = json.loads(raw) if raw else {}
                    if "error" in obj or not obj:
                        raise ValueError(f"No dataset response ({obj.get('error', 'empty')})")
                    if obj["id"][-1] != "time" or any(size != 1 for size in obj["size"][:-1]):
                        raise ValueError("Response is not a single series")
                    dims = obj["dimension"]
                    labels = {
                        d: next(iter(dims[d]["category"]["label"].values()))
                        for d in obj["id"]
                        if d != "time"
                    }
                    times = dims["time"]["category"]["index"]
                    values = obj.get("value", {})
                    if isinstance(values, list):
                        values = {str(i): v for i, v in enumerate(values) if v is not None}
                    periods = sorted(t for t, i in times.items() if values.get(str(i)) is not None)
                    if not periods:
                        raise ValueError("No nonmissing observations")
                    fields.update(
                        status="verified",
                        first_period=periods[0],
                        last_period=periods[-1],
                        observation_count=len(periods),
                        frequency=labels.get("freq"),
                        unit=labels.get("unit"),
                        seasonal_adjustment=labels.get("s_adj"),
                        response_labels=labels,
                        notes=[
                            f"Explicit candidate validated by response labels; dataset updated "
                            f"{obj.get('updated', 'unknown')}."
                        ],
                    )
                except (ValueError, KeyError, TypeError, StopIteration) as exc:
                    fields.update(status="failed", notes=[str(exc)])
                self.record(country, indicator, "Eurostat", code, ev, **fields)

    ECB_CANDIDATES = {
        "mro_rate": "FM.B.U2.EUR.4F.KR.MRR_FR.LEV",
        "deposit_rate": "FM.B.U2.EUR.4F.KR.DFR.LEV",
    }

    def ecb_explicit(self) -> None:
        self.records = [r for r in self.records if r["source"] != "ECB"]
        for indicator, key in self.ECB_CANDIDATES.items():
            flow, series = key.split(".", 1)
            url = (
                f"https://data-api.ecb.europa.eu/service/data/{flow}/{series}"
                "?format=csvdata&detail=full"
            )
            raw, ev = self.get(url, "text/csv")
            fields: dict[str, Any] = dict(
                exact_filter_or_key=key,
                notes=["Shared euro area policy rate, not a national central-bank rate."],
            )
            try:
                rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))) if raw else []
                valid = [r for r in rows if r.get("OBS_VALUE") not in (None, "")]
                if not valid:
                    raise ValueError("No observations")
                titles = {r.get("TITLE") for r in valid} - {None, ""}
                fields.update(
                    status="verified",
                    first_period=valid[0]["TIME_PERIOD"],
                    last_period=valid[-1]["TIME_PERIOD"],
                    observation_count=len(valid),
                    frequency=valid[-1].get("FREQ"),
                    unit=valid[-1].get("UNIT"),
                    response_labels={"TITLE": sorted(titles)},
                    notes=fields["notes"] + ["Event-dated series (changes on decision dates)."],
                )
            except (ValueError, KeyError, UnicodeError) as exc:
                fields.update(status="failed", notes=fields["notes"] + [str(exc)])
            self.record("EA", indicator, "ECB", key, ev, **fields)

    def oecd_explicit(self) -> None:
        """List the CLI series actually available per country (monthly); a model choice comes later."""
        self.records = [r for r in self.records if r["source"] != "OECD"]
        agency, flow, version = "OECD.SDD.STES", "DSD_STES@DF_CLI", "4.1"
        for country, ref in (
            ("BE", "BEL"),
            ("DE", "DEU"),
            ("FR", "FRA"),
            ("NL", "NLD"),
            ("US", "USA"),
        ):
            url = (
                f"https://sdmx.oecd.org/public/rest/data/{agency},{flow},{version}/{ref}.M......."
                "?lastNObservations=1&format=csvfilewithlabels"
            )
            raw, ev = self.get(url, "text/csv")
            fields: dict[str, Any] = dict(exact_filter_or_key=f"{ref}.M.......")
            try:
                rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))) if raw else []
                valid = [r for r in rows if r.get("OBS_VALUE") not in (None, "")]
                if not valid:
                    raise ValueError("No observations (key shape or coverage)")
                options = sorted(
                    {
                        " / ".join(
                            str(r.get(k, ""))
                            for k in (
                                "MEASURE",
                                "Measure",
                                "ADJUSTMENT",
                                "Adjustment",
                                "TRANSFORMATION",
                                "Transformation",
                            )
                        )
                        for r in valid
                    }
                )
                fields.update(
                    status="partial",
                    frequency="M",
                    last_period=max(r["TIME_PERIOD"] for r in valid),
                    observation_count=len(valid),
                    response_labels={"series": options},
                    notes=[
                        "Lists available monthly CLI series (latest obs only); the exact "
                        "measure/adjustment must be fixed in the Phase 3 connector."
                    ],
                )
            except (ValueError, KeyError, UnicodeError) as exc:
                fields.update(status="failed", notes=[str(exc)])
            self.record(country, "cli", "OECD", flow, ev, **fields)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    probe = Probe()
    for action in (
        probe.eurostat,
        probe.fred,
        probe.world_bank,
        lambda: probe.sdmx_discovery(
            "ECB",
            "https://data-api.ecb.europa.eu/service/dataflow/ECB/FM/latest?references=all",
            ("mro_rate", "deposit_rate"),
        ),
        # Dataflow list only (no references): the matching flow's structure is fetched separately.
        lambda: probe.sdmx_discovery(
            "OECD", "https://sdmx.oecd.org/public/rest/v1/dataflow/all/all/latest", ("cli",)
        ),
        probe.eurostat_explicit,
        probe.ecb_explicit,
        probe.oecd_explicit,
    ):
        action()
    result = {
        "generated_at_utc": utc(),
        "user_agent": UA,
        "ca_bundle": CA_SOURCE,
        "timeout_seconds": 20,
        "retries": 2,
        "records": probe.records,
        "requests": probe.requests,
        "limitations": [
            "SDMX ambiguous label selections fail closed; slices are partial coverage.",
            "FRED CSV does not establish units or seasonal adjustment.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"out": str(args.out), "requests": len(probe.requests), "records": len(probe.records)}
        )
    )


if __name__ == "__main__":
    main()
