"""As-of quarterly feature snapshots.

A snapshot for as-of quarter t may use an observation only if its reference period ended at least
`lag` days before the last day of t. The lags below are deliberately conservative publication
delays (the stored data are latest revisions and carry no release dates or vintages):

| input                        | lag (days after period end) | typical official release           |
|------------------------------|-----------------------------|------------------------------------|
| real GDP q/q and y/y         | 60                          | flash/advance ~30 days, t+60 full  |
| inflation (HICP rate / CPI)  | 30                          | HICP flash at month end, CPI ~t+13 |
| unemployment rate            | 45                          | Eurostat ~t+31, BLS ~t+5           |
| policy rate, ECB decisions   | 0                           | known on the effective date        |
| policy rate, FRED FEDFUNDS   | 7                           | monthly average, next business day |
| 10y yield and 3m rate        | 30                          | monthly averages, ~t+1 to t+15     |

So at the end of 2026-Q1 a snapshot sees GDP through 2025-Q4, inflation through 2026-02,
unemployment through 2026-01 and the policy rate in force. If the expected latest monthly value is
missing at the source (e.g. US October 2025, finding F-006) the previous month is used and the
staleness is recorded; a second missing month, or any GDP gap, excludes the snapshot.

The term spread (10-year government yield minus the 3-month rate) is the one leading indicator
available for every country from official sources; for euro-area members the short leg is the
shared euro-area 3-month rate (Eurostat publishes no national series).

Excluded on purpose (documented, not silently dropped): government debt (EU general government vs
US federal debt are not comparable), the US-only daily T10Y3M series (superseded by the monthly
term spread), the OECD CLI (no connector) and NBER dates (external reference, never a feature or
a target).
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field
from datetime import date, timedelta

from macropulse_economics.periods import period_end, shift

Series = dict[str, float]

LAG_DAYS = {
    "gdp": 60,
    "inflation": 30,
    "unemployment": 45,
    "policy_rate_event": 0,
    "policy_rate_monthly": 7,
    "rates_monthly": 30,
}
MAX_EXTRA_MONTHS = 1  # tolerated staleness for monthly inputs beyond the lag

FEATURES: tuple[tuple[str, str], ...] = (
    ("gdp_qoq_1", "Real GDP q/q growth, latest published quarter (%)"),
    ("gdp_qoq_2", "Real GDP q/q growth, quarter before that (%)"),
    ("gdp_yoy_1", "Real GDP y/y growth, latest published quarter (%)"),
    ("gdp_neg_4", "Negative q/q quarters among the last four published"),
    ("infl_yoy", "Inflation, latest published month (% y/y)"),
    ("infl_chg_6m", "Change in inflation over six months (pp)"),
    ("unemp", "Unemployment rate, latest published month (%)"),
    ("unemp_chg_6m", "Change in unemployment over six months (pp)"),
    ("rate", "Policy rate in force (%)"),
    ("rate_chg_4q", "Change in the policy rate over four quarters (pp)"),
    ("term_spread", "10-year yield minus 3-month rate, latest published month (pp)"),
)
FEATURE_NAMES: tuple[str, ...] = tuple(name for name, _ in FEATURES)

EXCLUDED_INPUTS = {
    "gov_debt_gdp": "EU general-government and US federal debt are not comparable definitions.",
    "yield_spread": "US-only daily series; superseded by the monthly term spread.",
    "cli": "Not published for BE/NL (finding F-002); not in the pre-registered feature set.",
    "business_confidence": "Synced since 2026-11-12; not in the pre-registered feature set.",
    "consumer_confidence": "Synced since 2026-11-12; not in the pre-registered feature set.",
    "nber_recession": "External reference chronology; never a feature or a target.",
}


@dataclass(frozen=True)
class CountryInputs:
    """Stored official series for one country, already derived by the documented transforms."""

    country: str
    gdp_qoq: Series  # quarterly q/q growth, %
    gdp_yoy: Series  # quarterly y/y growth, %
    inflation: Series  # monthly y/y, %
    unemployment: Series  # monthly, %
    policy_rate: Series  # monthly (FEDFUNDS) or event-dated (ECB decisions)
    policy_rate_event_dated: bool
    bond_yield: Series = field(default_factory=dict)  # monthly 10-year government yield, %
    short_rate: Series = field(default_factory=dict)  # monthly 3-month rate, %


@dataclass(frozen=True)
class Snapshot:
    country: str
    as_of: str
    values: dict[str, float]
    used: dict[str, str] = field(default_factory=dict)  # feature -> period it is based on
    stale: tuple[str, ...] = ()  # inputs that fell back to an older period


class _Indexed:
    """A series sorted by period end, for 'latest value published by date D' lookups."""

    def __init__(self, series: Series) -> None:
        items = sorted(series.items(), key=lambda kv: period_end(kv[0]))
        self.periods = [p for p, _ in items]
        self.values = [v for _, v in items]
        self.ends = [period_end(p) for p in self.periods]

    def latest(self, cutoff: date, lag_days: int) -> tuple[str, float] | None:
        i = bisect_right(self.ends, cutoff - timedelta(days=lag_days))
        if i == 0:
            return None
        return self.periods[i - 1], self.values[i - 1]


def _expected_latest_month(cutoff: date, lag_days: int) -> str:
    """The newest month whose end + lag is on or before the cut-off."""
    limit = cutoff - timedelta(days=lag_days)
    first_of_month = limit.replace(day=1)
    month_end = (first_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    latest = limit if limit == month_end else first_of_month - timedelta(days=1)
    return f"{latest.year}-{latest.month:02d}"


def _months_between(older: str, newer: str) -> int:
    oy, om = (int(x) for x in older.split("-"))
    ny, nm = (int(x) for x in newer.split("-"))
    return (ny - oy) * 12 + (nm - om)


class _Builder:
    def __init__(self, inputs: CountryInputs) -> None:
        self.inputs = inputs
        self.gdp_qoq = _Indexed(inputs.gdp_qoq)
        self.gdp_yoy = inputs.gdp_yoy
        self.inflation = _Indexed(inputs.inflation)
        self.unemployment = _Indexed(inputs.unemployment)
        self.rate = _Indexed(inputs.policy_rate)
        self.rate_lag = LAG_DAYS[
            "policy_rate_event" if inputs.policy_rate_event_dated else "policy_rate_monthly"
        ]

    def _monthly(
        self, series: _Indexed, raw: Series, lag: int, cutoff: date
    ) -> tuple[str, float, float, bool] | None:
        """(period, latest, change over 6 months, stale) or None when not computable."""
        found = series.latest(cutoff, lag)
        if found is None:
            return None
        period, value = found
        expected = _expected_latest_month(cutoff, lag)
        extra = _months_between(period, expected)
        if extra > MAX_EXTRA_MONTHS:
            return None
        earlier = raw.get(shift(period, -6))
        if earlier is None:
            return None
        return period, value, value - earlier, extra > 0

    def _gdp(self, as_of: str, cutoff: date) -> tuple[dict[str, float], dict[str, str]] | None:
        """GDP features; t-1 must be published and no GDP staleness is tolerated."""
        gdp = self.gdp_qoq.latest(cutoff, LAG_DAYS["gdp"])
        if gdp is None or gdp[0] != shift(as_of, -1):
            return None
        last_q = gdp[0]
        window = [shift(last_q, -k) for k in range(4)]
        growth = [self.inputs.gdp_qoq.get(p) for p in window]
        yoy = self.gdp_yoy.get(last_q)
        if any(g is None for g in growth) or yoy is None:
            return None
        g = [x for x in growth if x is not None]
        values = {
            "gdp_qoq_1": g[0],
            "gdp_qoq_2": g[1],
            "gdp_yoy_1": yoy,
            "gdp_neg_4": float(sum(x < 0 for x in g)),
        }
        used = {
            "gdp_qoq_1": last_q,
            "gdp_qoq_2": window[1],
            "gdp_yoy_1": last_q,
            "gdp_neg_4": last_q,
        }
        return values, used

    def _policy_rate(self, cutoff: date) -> tuple[tuple[str, float], tuple[str, float]] | None:
        now = self.rate.latest(cutoff, self.rate_lag)
        year_ago = self.rate.latest(cutoff.replace(year=cutoff.year - 1), self.rate_lag)
        if now is None or year_ago is None:
            return None
        if not self.inputs.policy_rate_event_dated:
            expected = _expected_latest_month(cutoff, self.rate_lag)
            if _months_between(now[0], expected) > MAX_EXTRA_MONTHS:
                return None
        return now, year_ago

    def snapshot(self, as_of: str) -> Snapshot | None:
        cutoff = period_end(as_of)
        stale: list[str] = []
        gdp = self._gdp(as_of, cutoff)
        if gdp is None:
            return None
        values, used = gdp

        infl = self._monthly(self.inflation, self.inputs.inflation, LAG_DAYS["inflation"], cutoff)
        unemp = self._monthly(
            self.unemployment, self.inputs.unemployment, LAG_DAYS["unemployment"], cutoff
        )
        if infl is None or unemp is None:
            return None
        values |= {
            "infl_yoy": infl[1],
            "infl_chg_6m": infl[2],
            "unemp": unemp[1],
            "unemp_chg_6m": unemp[2],
        }
        used |= {
            "infl_yoy": infl[0],
            "infl_chg_6m": infl[0],
            "unemp": unemp[0],
            "unemp_chg_6m": unemp[0],
        }
        stale += [name for name, m in (("inflation", infl), ("unemployment", unemp)) if m[3]]

        rate = self._policy_rate(cutoff)
        spread = self._spread(cutoff)
        if rate is None or spread is None:
            return None
        now, year_ago = rate
        values |= {"rate": now[1], "rate_chg_4q": now[1] - year_ago[1]}
        used |= {"rate": now[0], "rate_chg_4q": now[0]}
        values["term_spread"] = spread[1]
        used["term_spread"] = spread[0]
        if spread[2]:
            stale.append("term_spread")
        return Snapshot(self.inputs.country, as_of, values, used, tuple(stale))

    def _spread(self, cutoff: date) -> tuple[str, float, bool] | None:
        """(month, 10y minus 3m, stale) for the newest month both legs were published."""
        expected = _expected_latest_month(cutoff, LAG_DAYS["rates_monthly"])
        for back in range(MAX_EXTRA_MONTHS + 1):
            month = shift(expected, -back)
            long_rate = self.inputs.bond_yield.get(month)
            short = self.inputs.short_rate.get(month)
            if long_rate is not None and short is not None:
                return month, long_rate - short, back > 0
        return None


def snapshots(inputs: CountryInputs, first_as_of: str, last_as_of: str) -> list[Snapshot]:
    """Every computable as-of snapshot for one country, oldest first."""
    builder = _Builder(inputs)
    out: list[Snapshot] = []
    q = first_as_of
    while period_end(q) <= period_end(last_as_of):
        snap = builder.snapshot(q)
        if snap is not None:
            out.append(snap)
        q = shift(q, 1)
    return out
