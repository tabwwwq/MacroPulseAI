"""Crisis time machine: what the model could have said at a past as-of quarter, and what followed.

The probability is the stored **walk-forward** estimate: for an as-of quarter in year Y it comes
from a model fitted only on as-of quarters t with t + H <= Y-Q1 - 1, whose outcomes were published
by the end of Y-Q1 (see `macropulse_ml.splits`). The inputs are rebuilt with the same publication
lags as in training. Neither uses today's knowledge of what happened next — but the numbers are
today's revised data, not the figures published then, so every replay is labelled a
*revised-data / release-lag approximation*.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from macropulse_api.errors import ApiError
from macropulse_api.models import ModelPrediction, ModelVersion
from macropulse_api.services import inference
from macropulse_api.services.series_data import load_indicator, resolve_indicator
from macropulse_api.services.training import country_inputs
from macropulse_economics.periods import period_end, shift
from macropulse_ml.features import FEATURES, LAG_DAYS, CountryInputs, Snapshot
from macropulse_ml.metrics import THRESHOLD
from macropulse_ml.target import quarter_index, technical_recessions

BASIS_LABEL = "Revised-data / release-lag approximation"
OUT_OF_SAMPLE = ("development", "heldout", "unlabelled")
LABELS = dict(FEATURES)
FEATURE_INPUT = {
    "gdp_qoq_1": "gdp",
    "gdp_qoq_2": "gdp",
    "gdp_yoy_1": "gdp",
    "gdp_neg_4": "gdp",
    "infl_yoy": "inflation",
    "infl_chg_6m": "inflation",
    "unemp": "unemployment",
    "unemp_chg_6m": "unemployment",
    "rate": "policy_rate",
    "rate_chg_4q": "policy_rate",
    "term_spread": "rates_monthly",
}
# Snapshot staleness names -> the input they refer to.
STALE_INPUT = {
    "inflation": "inflation",
    "unemployment": "unemployment",
    "term_spread": "rates_monthly",
}
# A false alarm starting during a recession or this many quarters after it is tagged: the
# model is still reacting to the slump while the next quarters recover.
RECOVERY_QUARTERS = 2
CRISES = (
    ("2008-Q2", "Global financial crisis"),
    ("2011-Q3", "Euro-area debt crisis"),
    ("2019-Q4", "Eve of COVID-19"),
    ("2022-Q2", "Energy-price shock"),
)


def _lag_days(feature: str, event_dated: bool) -> int:
    key = FEATURE_INPUT[feature]
    if key == "policy_rate":
        key = "policy_rate_event" if event_dated else "policy_rate_monthly"
    return LAG_DAYS[key]


def basis(iso2: str, *, fred_key_configured: bool) -> dict[str, Any]:
    """How faithful a replay can be for this country, stated before any number."""
    if iso2 == "US":
        vintage = (
            "ALFRED keeps the US figures as first published. With a server-side FRED_API_KEY "
            f"({'configured' if fred_key_configured else 'not configured'}) `macropulse "
            "vintages-sync` stores the revision history of US GDP, CPI and unemployment, shown as "
            "'first release vs today' on the country page. This replay uses today's revised FRED "
            "data; the vintage comparison scores the same fold model on the figures as first "
            "published."
        )
    else:
        vintage = (
            "Eurostat and the ECB serve the latest revision of each series; the figures as first "
            "published are not stored, so no vintage-backed replay is possible."
        )
    return {
        "kind": "revised_data_release_lag_approximation",
        "label": BASIS_LABEL,
        "detail": (
            "Inputs are today's revised values, cut at the as-of date with conservative "
            "publication lags: a value counts as known only once its period had ended and the "
            "lag had passed. First estimates (especially of GDP) were often different."
        ),
        "vintages_available": False,
        "vintage_note": vintage,
        "lag_assumptions_days": dict(LAG_DAYS),
    }


def _walk_forward(session: Session, version_id: str, iso2: str) -> list[ModelPrediction]:
    rows = session.scalars(
        select(ModelPrediction).where(
            ModelPrediction.model_version_id == version_id,
            ModelPrediction.country == iso2,
            ModelPrediction.split.in_(OUT_OF_SAMPLE),
        )
    ).all()
    return sorted(rows, key=lambda r: quarter_index(r.as_of))


def _baseline_id(session: Session, v: ModelVersion) -> str | None:
    return session.scalar(
        select(ModelVersion.id).where(
            ModelVersion.run_id == v.run_id,
            ModelVersion.horizon == v.horizon,
            ModelVersion.model_key == "prevalence",
        )
    )


def verdict(probability: float, label: int | None) -> str | None:
    if label is None:
        return None
    flagged = probability >= THRESHOLD
    if label == 1:
        return "hit" if flagged else "miss"
    return "false_alarm" if flagged else "correct_quiet"


def _nber(session: Session, window: list[str]) -> dict[str, Any] | None:
    """US only: NBER recession months inside the outcome window (external reference)."""
    try:
        data = load_indicator(session, "US", resolve_indicator("nber_recession"))
    except ApiError:
        return None
    months = [f"{q[:4]}-{(int(q[-1]) - 1) * 3 + k:02d}" for q in window for k in (1, 2, 3)]
    values = dict(data.points)
    known = [m for m in months if m in values]
    return {
        "name": "NBER recession months (external reference, not the model's target)",
        "months_in_window": sum(1 for m in known if values[m] >= 0.5),
        "months_known": len(known),
        "window_months": len(months),
        "source": f"{data.mapping.source_id.upper()} {data.mapping.series_key}",
    }


def _gdp_path(inputs: CountryInputs, as_of: str, horizon: int) -> list[dict[str, Any]]:
    """The last eight GDP quarters known at the as-of, then the outcome window as published
    later. All values are today's revisions."""
    cutoff = period_end(as_of)
    lag = timedelta(days=LAG_DAYS["gdp"])
    known = sorted((p for p in inputs.gdp_qoq if period_end(p) + lag <= cutoff), key=quarter_index)[
        -8:
    ]
    out = [{"period": p, "value": inputs.gdp_qoq[p], "known_at_as_of": True} for p in known]
    later_from = shift(known[-1], 1) if known else shift(as_of, 1)
    q = later_from
    while quarter_index(q) <= quarter_index(shift(as_of, horizon)):
        if q in inputs.gdp_qoq:
            out.append({"period": q, "value": inputs.gdp_qoq[q], "known_at_as_of": False})
        q = shift(q, 1)
    return out


def _unavailable_reason(iso2: str, as_of: str, first: str) -> str:
    if quarter_index(as_of) < quarter_index(first):
        return (
            f"No out-of-sample estimate before {first}: the first walk-forward model needs enough "
            "earlier technical recessions to learn from, so earlier quarters could only be shown "
            "as an in-sample fit."
        )
    return f"No walk-forward estimate for {iso2} at {as_of} (inputs incomplete then)."


def _known_inputs(snap: Snapshot | None, *, event_dated: bool) -> list[dict[str, Any]]:
    if snap is None:
        return []
    stale = {STALE_INPUT.get(x) for x in snap.stale}
    return [
        {
            "feature": name,
            "label": LABELS[name],
            "value": snap.values[name],
            "period": snap.used.get(name),
            "publication_lag_days": _lag_days(name, event_dated),
            "stale": FEATURE_INPUT[name] in stale,
        }
        for name, _label in FEATURES
    ]


def _baseline_probability(session: Session, v: ModelVersion, iso2: str, as_of: str) -> float | None:
    baseline_id = _baseline_id(session, v)
    if baseline_id is None:
        return None
    return session.scalar(
        select(ModelPrediction.probability).where(
            ModelPrediction.model_version_id == baseline_id,
            ModelPrediction.country == iso2,
            ModelPrediction.as_of == as_of,
            ModelPrediction.split.in_(OUT_OF_SAMPLE),
        )
    )


def _outcome_status(label: int | None, inputs: CountryInputs, window: list[str]) -> str:
    if label is not None:
        return "observed"
    last_gdp = max(inputs.gdp_qoq, key=quarter_index) if inputs.gdp_qoq else None
    if last_gdp is None or quarter_index(window[-1]) > quarter_index(last_gdp):
        return "censored"
    return "missing"


def _selection_note(split: str, trained_through: str) -> str:
    if split == "development":
        return (
            "Development year: the fitted weights use only outcomes through as-of "
            f"{trained_through}, but the model type was chosen in 2026 by comparing the 2000 to "
            "2014 backtests, which include this year."
        )
    if split == "heldout":
        return (
            f"Held-out year: neither the weights (outcomes through as-of {trained_through}) nor "
            "the choice of model type used outcomes from 2015 onwards."
        )
    return "The outcome window has not been fully published yet."


def replay(
    session: Session,
    iso2: str,
    horizon: int,
    as_of: str,
    *,
    fred_key_configured: bool,
    today: date | None = None,
) -> dict[str, Any]:
    day = today or datetime.now(UTC).date()
    if period_end(as_of) > day:
        raise ApiError(422, "invalid_as_of", f"As-of quarter {as_of} has not ended yet.")
    v = inference.published_version(session, horizon)
    rows = _walk_forward(session, v.id, iso2)
    if not rows:
        raise ApiError(
            404, "replay_unavailable", f"The published model has no estimates for {iso2}."
        )
    first, last = rows[0].as_of, rows[-1].as_of
    row = next((r for r in rows if r.as_of == as_of), None)
    if row is None:
        raise ApiError(
            404,
            "replay_unavailable",
            _unavailable_reason(iso2, as_of, first),
            {"first": first, "last": last},
        )

    inputs, _ = country_inputs(session, iso2)
    snap = inference.snapshot_for(inputs, as_of)
    cutoff = period_end(as_of)
    known = _known_inputs(snap, event_dated=inputs.policy_rate_event_dated)
    baseline = _baseline_probability(session, v, iso2, as_of)

    fold = row.fold_year or int(as_of[:4])
    folds: list[dict[str, Any]] = v.evaluation.get("folds", [])
    fold_info: dict[str, Any] = next((f for f in folds if f.get("year") == fold), {})
    trained_through = shift(f"{fold}-Q1", -1 - horizon)
    window = [shift(as_of, k) for k in range(1, horizon + 1)]
    events = [
        {"start": a, "end": b}
        for a, b in technical_recessions(inputs.gdp_qoq)
        if quarter_index(a) <= quarter_index(window[-1])
        and quarter_index(b) >= quarter_index(window[0])
    ]

    caveats = [
        f"{BASIS_LABEL}: today's revised data, cut at {cutoff} with conservative publication lags.",
        "The feature set and lag assumptions were designed in 2026, with hindsight about which "
        "inputs matter.",
        "A walk-forward estimate is what this method would have said, not a forecast anyone "
        "published at the time.",
    ]

    return {
        "country": iso2,
        "horizon": horizon,
        "as_of": as_of,
        "cutoff": cutoff,
        "event_definition": (
            f"Technical recession within the next {horizon} quarters: two consecutive quarters of "
            f"negative real-GDP q/q growth inside {window[0]} … {window[-1]}."
        ),
        "basis": basis(iso2, fred_key_configured=fred_key_configured),
        "model": {
            "id": v.id,
            "name": v.name,
            "run_id": v.run_id,
            "fold_year": fold,
            "trained_through_as_of": trained_through,
            "training_rows": fold_info.get("train_rows"),
            "split": row.split,
            "selection_note": _selection_note(row.split, trained_through),
        },
        "probability": row.probability,
        "band": inference.risk_band(row.probability),
        "baseline_probability": baseline,
        "threshold": THRESHOLD,
        "inputs": known,
        "inputs_note": None
        if snap is not None
        else "The input set could not be rebuilt from the stored series for this quarter.",
        "gdp": _gdp_path(inputs, as_of, horizon),
        "outcome": {
            "status": _outcome_status(row.label, inputs, window),
            "label": row.label,
            "window": window,
            "events": events,
            "verdict": verdict(row.probability, row.label),
        },
        "nber": _nber(session, window) if iso2 == "US" else None,
        "range": {"first": first, "last": last},
        "caveats": caveats,
        "computed_at": datetime.now(UTC),
    }


def episodes(session: Session, iso2: str, horizon: int) -> dict[str, Any]:
    """Every realised technical recession with what the model said in the quarters before it
    began, every false alarm, and the confusion counts at the 50 % threshold."""
    v = inference.published_version(session, horizon)
    rows = _walk_forward(session, v.id, iso2)
    if not rows:
        raise ApiError(
            404, "replay_unavailable", f"The published model has no estimates for {iso2}."
        )
    by_q = {r.as_of: r for r in rows}
    inputs, _ = country_inputs(session, iso2)
    first = rows[0].as_of

    recessions = []
    for start, end in technical_recessions(inputs.gdp_qoq):
        # As-of quarters before the first negative quarter whose window holds the first pair.
        warn = [shift(start, -k) for k in range(horizon - 1, 0, -1)]
        scored = [by_q[q] for q in warn if q in by_q]
        if not scored:
            status = "not_evaluable"
            note: str | None = (
                f"No walk-forward estimate for {', '.join(warn)} (first estimate: {first})."
            )
            peak = None
        else:
            peak = max(scored, key=lambda r: r.probability)
            status = "warned" if peak.probability >= THRESHOLD else "missed"
            note = (
                None if len(scored) == len(warn) else "Only part of the warning window is scored."
            )
        recessions.append(
            {
                "start": start,
                "end": end,
                "warning_as_of": warn,
                "max_probability": peak.probability if peak else None,
                "max_at": peak.as_of if peak else None,
                "status": status,
                "note": note,
            }
        )

    alarms: list[dict[str, Any]] = []
    for r in rows:
        if r.label != 0 or r.probability < THRESHOLD:
            continue
        prev = alarms[-1] if alarms else None
        if prev and quarter_index(r.as_of) == quarter_index(prev["end"]) + 1:
            prev["end"] = r.as_of
            prev["quarters"] += 1
            if r.probability > prev["max_probability"]:
                prev["max_probability"], prev["max_at"] = r.probability, r.as_of
        else:
            alarms.append(
                {
                    "start": r.as_of,
                    "end": r.as_of,
                    "quarters": 1,
                    "max_probability": r.probability,
                    "max_at": r.as_of,
                }
            )

    spans = technical_recessions(inputs.gdp_qoq)
    for alarm in alarms:
        a0 = quarter_index(alarm["start"])
        near = next(
            (
                (a, b)
                for a, b in spans
                if quarter_index(a) <= a0 <= quarter_index(b) + RECOVERY_QUARTERS
            ),
            None,
        )
        alarm["follows_recession"] = f"{near[0]} to {near[1]}" if near else None

    labelled = [r for r in rows if r.label is not None]
    confusion = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for r in labelled:
        flagged = r.probability >= THRESHOLD
        key = ("tp" if flagged else "fn") if r.label == 1 else ("fp" if flagged else "tn")
        confusion[key] += 1
    return {
        "country": iso2,
        "horizon": horizon,
        "model_id": v.id,
        "model_name": v.name,
        "threshold": THRESHOLD,
        "first_as_of": first,
        "last_as_of": rows[-1].as_of,
        "last_labelled_as_of": labelled[-1].as_of if labelled else None,
        "confusion": confusion,
        "recessions": recessions,
        "false_alarms": alarms,
        "note": (
            f"Warning window: the {horizon - 1} as-of quarter{'s' if horizon > 2 else ''} before "
            "the first negative quarter whose outcome window contains the first negative pair. "
            f"'Warned' means a walk-forward estimate reached {THRESHOLD:.0%}. Recessions before "
            f"{first} cannot be evaluated out of sample."
        ),
    }
