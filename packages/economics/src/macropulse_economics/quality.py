"""Data-quality rules run on every fetched series. Results are stored per ingestion run and never
alter the data: they flag gaps, staleness, implausible values and provisional flags."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from itertools import pairwise

from macropulse_economics.connectors.base import FetchResult
from macropulse_economics.periods import days_since_end, period_start, shift

# Oldest acceptable age of the latest observation, in days after the END of its period. Generous
# relative to normal release lags (monthly HICP/unemployment ~t+30-45, quarterly GDP t+30-60,
# quarterly government debt ~t+110-120, daily market data t+1), so a warning means a release was
# probably missed rather than "not yet due". See vault/50 Methodology for the release-lag notes.
MAX_AGE_DAYS = {"monthly": 90, "quarterly": 150, "daily": 14}

# SDMX OBS_STATUS codes that mean "normal value" (ECB uses `A`); they are not flags.
NORMAL_STATUS = frozenset({"A"})


@dataclass(frozen=True, slots=True)
class CheckResult:
    rule: str
    status: str  # pass | warn | fail
    detail: str


def _gaps(periods: list[str]) -> list[str]:
    missing: list[str] = []
    ordered = sorted(set(periods), key=period_start)
    for prev, cur in pairwise(ordered):
        expected = shift(prev, 1)
        while expected != cur and len(missing) < 1000:
            missing.append(expected)
            expected = shift(expected, 1)
    return missing


def run_checks(result: FetchResult, today: date) -> list[CheckResult]:
    req = result.request
    obs = result.observations
    checks: list[CheckResult] = []

    if not obs:
        return [CheckResult("non_empty", "fail", "Source returned no observations.")]
    checks.append(CheckResult("non_empty", "pass", f"{len(obs)} observations."))

    periods = [o.period for o in obs]
    if len(set(periods)) != len(periods):
        checks.append(CheckResult("unique_periods", "fail", "Duplicate periods in the response."))
    else:
        checks.append(CheckResult("unique_periods", "pass", "No duplicate periods."))

    if req.frequency in ("monthly", "quarterly"):
        missing = _gaps(periods)
        if missing:
            shown = ", ".join(missing[:5]) + (" …" if len(missing) > 5 else "")
            checks.append(
                CheckResult(
                    "gaps", "warn", f"{len(missing)} missing period(s) inside the range: {shown}"
                )
            )
        else:
            checks.append(CheckResult("gaps", "pass", f"Continuous {periods[0]} … {periods[-1]}."))

    latest = obs[-1].period
    if req.frequency in MAX_AGE_DAYS:
        age = days_since_end(latest, today)
        limit = MAX_AGE_DAYS[req.frequency]
        status = "pass" if age <= limit else "warn"
        checks.append(
            CheckResult(
                "freshness",
                status,
                f"Latest period {latest} ended {age} days before {today} (limit {limit}).",
            )
        )
    else:
        checks.append(
            CheckResult("freshness", "pass", f"Event-dated series; latest change {latest}.")
        )

    values = [o.value for o in obs]
    lo, hi = min(values), max(values)
    if (
        "chained" in req.unit.lower()
        or "chain-linked" in req.unit.lower()
        or "index" in req.unit.lower()
    ):
        bad = lo <= 0
        rng = "levels must be positive"
    else:
        bad = lo < -50 or hi > 300
        rng = "rates expected within [-50, 300]"
    checks.append(
        CheckResult(
            "plausible_range", "warn" if bad else "pass", f"min {lo:g}, max {hi:g} ({rng})."
        )
    )

    flagged = [o for o in obs if o.obs_status and o.obs_status not in NORMAL_STATUS]
    if flagged:
        flags = sorted({o.obs_status or "" for o in flagged})
        checks.append(
            CheckResult(
                "source_flags",
                "pass",
                f"{len(flagged)} observation(s) flagged by the source: {', '.join(flags)} "
                "(e.g. p=provisional, e=estimated, b=break).",
            )
        )

    for w in result.warnings:
        checks.append(CheckResult("source_warning", "warn", w))
    return checks
