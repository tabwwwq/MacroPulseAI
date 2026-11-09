"""Deterministic synthetic panels for ML tests. They exercise mechanics (alignment, censoring,
purging, leakage); they are never used to report model quality."""

from __future__ import annotations

import numpy as np

from macropulse_economics.periods import shift
from macropulse_ml.features import CountryInputs


def synthetic_inputs(
    country: str,
    seed: int,
    first_year: int = 1975,
    last_quarter: str = "2026-Q3",
    event_dated_rate: bool = False,
) -> CountryInputs:
    rng = np.random.default_rng(seed)
    quarters: list[str] = []
    q = f"{first_year}-Q1"
    while q != shift(last_quarter, 1):
        quarters.append(q)
        q = shift(q, 1)
    growth = 0.5 + 0.3 * rng.standard_normal(len(quarters))
    stress = np.zeros(len(quarters))
    start = 12 + int(rng.integers(0, 6))
    while start + 3 < len(quarters):
        growth[start : start + 2] = [-0.6, -0.4]  # a technical recession
        stress[max(0, start - 4) : start + 2] = np.linspace(
            0.2, 1.4, len(stress[max(0, start - 4) : start + 2])
        )
        start += 20 + int(rng.integers(0, 10))
    gdp_qoq = {p: round(float(g), 3) for p, g in zip(quarters, growth, strict=True)}
    level = np.cumprod(1 + growth / 100)
    gdp_yoy = {
        quarters[i]: round(float((level[i] / level[i - 4] - 1) * 100), 3)
        for i in range(4, len(quarters))
    }

    months: list[str] = []
    m = f"{first_year}-01"
    last_month = f"{last_quarter[:4]}-{int(last_quarter[-1]) * 3:02d}"
    while m != shift(last_month, 1):
        months.append(m)
        m = shift(m, 1)
    month_stress = np.repeat(stress, 3)[: len(months)]
    unemployment = {
        mm: round(float(6 + s + 0.1 * rng.standard_normal()), 2)
        for mm, s in zip(months, month_stress, strict=True)
    }
    inflation = {mm: round(float(2 + 0.4 * rng.standard_normal()), 2) for mm in months}
    if event_dated_rate:
        rate = {
            f"{mm}-15": round(float(3 - s), 2)
            for mm, s in zip(months[::4], month_stress[::4], strict=True)
        }
    else:
        rate = {
            mm: round(float(3 - s + 0.05 * rng.standard_normal()), 2)
            for mm, s in zip(months, month_stress, strict=True)
        }
    # the curve flattens ahead of the synthetic recessions
    short = {mm: round(float(3 - s), 2) for mm, s in zip(months, month_stress, strict=True)}
    bond = {mm: round(float(4.5 - 2.2 * s), 2) for mm, s in zip(months, month_stress, strict=True)}
    return CountryInputs(
        country, gdp_qoq, gdp_yoy, inflation, unemployment, rate, event_dated_rate, bond, short
    )
