"""Idempotently mirror the static country/source registry into the database."""

from __future__ import annotations

from dataclasses import asdict

from sqlalchemy.orm import Session

from macropulse_api.models import Country, DataSource
from macropulse_economics import COUNTRIES, SOURCES


def sync_registry(session: Session) -> tuple[int, int]:
    """Upsert registry rows. Returns (countries, sources) written. Never deletes user data."""
    for country_def in COUNTRIES:
        values = {
            k: str(v) if k in {"policy_rate_scope", "target_support"} else v
            for k, v in asdict(country_def).items()
        }
        country = session.get(Country, country_def.iso2)
        if country is None:
            session.add(Country(**values))
        else:
            for key, value in values.items():
                setattr(country, key, value)
    for source_def in SOURCES:
        values = asdict(source_def)
        source = session.get(DataSource, source_def.id)
        if source is None:
            session.add(DataSource(**values))
        else:
            for key, value in values.items():
                setattr(source, key, value)
    session.commit()
    return len(COUNTRIES), len(SOURCES)
