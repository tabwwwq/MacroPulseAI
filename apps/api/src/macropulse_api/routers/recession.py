"""Technical-recession estimates: a live inference round trip and the out-of-sample history."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Request
from sqlalchemy import select

from macropulse_api.deps import SessionDep
from macropulse_api.errors import ApiError
from macropulse_api.models import ModelPrediction, ModelVersion
from macropulse_api.routers.countries import unsupported_country
from macropulse_api.schemas import ErrorResponse, RecessionEstimate, RecessionHistory
from macropulse_api.services.inference import estimate, published_version
from macropulse_api.services.series_data import load_indicator, resolve_indicator
from macropulse_economics import get_country
from macropulse_ml.target import quarter_index, technical_recessions

router = APIRouter(prefix="/api/recession", tags=["recession"])

CountryQuery = Annotated[str, Query(pattern=r"^[A-Za-z]{2}$", description="ISO alpha-2 code.")]
HorizonQuery = Annotated[int, Query(description="Quarters ahead: 2 or 4.")]
HORIZONS = (2, 4)
AsOfQuery = Annotated[
    str | None,
    Query(pattern=r"^\d{4}-Q[1-4]$", description="As-of quarter; omit for the latest available."),
]
ERRORS = {
    404: {"model": ErrorResponse, "description": "Inputs not available for this as-of quarter."},
    422: {"model": ErrorResponse, "description": "Unsupported country, horizon or as-of."},
    503: {"model": ErrorResponse, "description": "No trained model / artifact / synced data."},
}


def event_definition(horizon: int) -> str:
    return (
        f"Technical recession within the next {horizon} quarters: at least one pair of consecutive "
        f"quarters with negative quarter-on-quarter real-GDP growth entirely inside t+1 … "
        f"t+{horizon}, where t is the as-of quarter. Zero growth is not negative. This is not an "
        "official recession call (for the US, NBER dates are a separate reference)."
    )


def limitations(iso2: str, track: dict[str, object]) -> list[str]:
    out = [
        "An analytical estimate from a statistical model, not a forecast of certainty and not "
        "investment advice.",
        "Few technical recessions per country: metrics rest on small event counts.",
        "Inputs are latest revised data with conservative publication lags — not the vintages "
        "available at the time.",
        "No confidence interval is shown: with this few events an interval would mostly reflect "
        "sampling noise. The measured track record is the uncertainty statement.",
    ]
    if track.get("beats_baseline_heldout") is False:
        out.insert(
            1,
            "On the held-out years (2015 onwards) this model did not beat the historical base rate "
            "(e.g. the COVID-2020 recession was not foreseeable from these inputs).",
        )
    if iso2 == "US":
        out.append("NBER recession dates are an external reference, never the training target.")
    else:
        out.append(
            "Euro-area members share the ECB policy rate and the euro-area 3-month rate; only the "
            "10-year yield is national."
        )
    return out


def _check(country: str, horizon: int) -> str:
    if get_country(country) is None:
        raise unsupported_country(country)
    if horizon not in HORIZONS:
        raise ApiError(
            422,
            "unsupported_horizon",
            f"Horizon {horizon} is not supported.",
            {"supported": list(HORIZONS)},
        )
    return country.upper()


@router.get(
    "/predict",
    response_model=RecessionEstimate,
    summary="Probability of a technical recession within 2 or 4 quarters (live inference)",
    responses=ERRORS,  # type: ignore[arg-type]
)
def predict(
    request: Request,
    session: SessionDep,
    country: CountryQuery,
    horizon: HorizonQuery,
    as_of: AsOfQuery = None,
) -> RecessionEstimate:
    iso = _check(country, horizon)
    result = estimate(
        session, iso, horizon, as_of, models_dir=request.app.state.settings.models_dir
    )
    return RecessionEstimate(
        **result,
        event_definition=event_definition(horizon),
        limitations=limitations(iso, result["track_record"]),
    )


@router.get(
    "/history",
    response_model=RecessionHistory,
    summary="Out-of-sample walk-forward probabilities with realised technical recessions",
    responses=ERRORS,  # type: ignore[arg-type]
)
def history(session: SessionDep, country: CountryQuery, horizon: HorizonQuery) -> RecessionHistory:
    iso = _check(country, horizon)
    v = published_version(session, horizon)

    def points(version_id: str) -> list[dict[str, object]]:
        rows = session.scalars(
            select(ModelPrediction).where(
                ModelPrediction.model_version_id == version_id,
                ModelPrediction.country == iso,
            )
        ).all()
        return [
            {
                "as_of": r.as_of,
                "probability": r.probability,
                "label": r.label,
                "split": r.split,
                "fold_year": r.fold_year,
            }
            for r in sorted(rows, key=lambda r: (quarter_index(r.as_of), r.split == "live"))
        ]

    baseline_id = session.scalar(
        select(ModelVersion.id).where(
            ModelVersion.run_id == v.run_id,
            ModelVersion.horizon == horizon,
            ModelVersion.model_key == "prevalence",
        )
    )
    try:
        gdp = dict(load_indicator(session, iso, resolve_indicator("real_gdp_qoq")).points)
    except ApiError:
        gdp = {}
    pts = points(v.id)
    if not pts:
        raise ApiError(
            404, "history_unavailable", f"The published model has no estimates for {iso}."
        )
    return RecessionHistory(
        country=iso,
        horizon=horizon,
        model_id=v.id,
        model_name=v.name,
        points=pts,
        baseline=[p for p in points(baseline_id) if p["split"] != "live"] if baseline_id else [],
        recessions=[{"start": a, "end": b} for a, b in technical_recessions(gdp)],
        note=(
            "Each historical probability comes from a model trained only on data whose outcomes "
            "were known before that year (walk-forward). `live` is the current estimate of the "
            "published model; `unlabelled` quarters have no observed outcome yet."
        ),
    )
