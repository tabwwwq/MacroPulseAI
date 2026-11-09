"""Pooled country-by-as-of panel with features and horizon labels."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from macropulse_ml.features import FEATURE_NAMES, CountryInputs, Snapshot, snapshots
from macropulse_ml.target import (
    HORIZONS,
    LabelStatus,
    quarter_index,
    technical_recession_label,
    technical_recessions,
)


@dataclass(frozen=True)
class Row:
    country: str
    as_of: str
    q: int  # quarter index of as_of
    x: tuple[float, ...]
    labels: dict[int, int | None]
    used: dict[str, str]
    stale: tuple[str, ...]


@dataclass
class Panel:
    rows: list[Row]
    feature_names: tuple[str, ...] = FEATURE_NAMES
    label_status: dict[int, Counter[str]] = field(default_factory=dict)
    events: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    last_observed: dict[str, str] = field(default_factory=dict)

    def matrix(self, idx: list[int]) -> NDArray[np.float64]:
        return np.array([self.rows[i].x for i in idx], dtype=np.float64).reshape(len(idx), -1)

    def target(self, idx: list[int], horizon: int) -> NDArray[np.int64]:
        values = [self.rows[i].labels[horizon] for i in idx]
        if any(v is None for v in values):
            raise ValueError("Unlabelled rows cannot be used as targets")
        return np.array(values, dtype=np.int64)

    def labelled(self, horizon: int) -> list[int]:
        return [i for i, r in enumerate(self.rows) if r.labels[horizon] is not None]


def build_panel(
    inputs: list[CountryInputs],
    first_as_of: str,
    last_as_of: str,
    horizons: tuple[int, ...] = HORIZONS,
) -> Panel:
    rows: list[Row] = []
    status: dict[int, Counter[str]] = {h: Counter() for h in horizons}
    events: dict[str, list[tuple[str, str]]] = {}
    last_observed: dict[str, str] = {}
    for c in inputs:
        if not c.gdp_qoq:
            continue
        last = max(c.gdp_qoq, key=quarter_index)
        last_observed[c.country] = last
        events[c.country] = technical_recessions(c.gdp_qoq)
        snaps: list[Snapshot] = snapshots(c, first_as_of, last_as_of)
        for s in snaps:
            labels: dict[int, int | None] = {}
            for h in horizons:
                lab = technical_recession_label(c.gdp_qoq, s.as_of, h, last)
                status[h][lab.status.value] += 1
                labels[h] = lab.value if lab.status is LabelStatus.OBSERVED else None
            rows.append(
                Row(
                    country=c.country,
                    as_of=s.as_of,
                    q=quarter_index(s.as_of),
                    x=tuple(s.values[name] for name in FEATURE_NAMES),
                    labels=labels,
                    used=s.used,
                    stale=s.stale,
                )
            )
    rows.sort(key=lambda r: (r.q, r.country))
    return Panel(rows, FEATURE_NAMES, status, events, last_observed)
