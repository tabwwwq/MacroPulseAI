"""Shared fixtures for the ML tests (synthetic data; mechanics only, never model quality)."""

from __future__ import annotations

import pytest
from ml_synthetic import synthetic_inputs

from macropulse_ml.features import CountryInputs


@pytest.fixture
def two_countries() -> list[CountryInputs]:
    return [synthetic_inputs("AA", 1), synthetic_inputs("BB", 2, event_dated_rate=True)]
