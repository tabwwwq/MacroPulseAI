"""Expanding-window, horizon-purged walk-forward folds over the pooled panel.

Fold for calendar year Y: test rows are the as-of quarters of Y (all countries). Training rows are
labelled rows whose label window had fully ended before the first test quarter could be scored:
a label for as-of t uses GDP for t+1 … t+H, and at as-of s (the first test quarter) GDP is published
only through s-1, so training needs t + H <= s - 1. The split is on time for every country at once,
so no country's later data informs another country's earlier test quarter.
"""

from __future__ import annotations

from dataclasses import dataclass

from macropulse_ml.panel import Panel
from macropulse_ml.target import quarter_index


@dataclass(frozen=True)
class Fold:
    year: int
    train: list[int]  # labelled training rows
    test: list[int]  # every row of the test year (labelled or not)
    train_max_q: int
    test_min_q: int


def walk_forward(
    panel: Panel, horizon: int, first_year: int, last_year: int, min_train_events: int = 8
) -> tuple[list[Fold], list[str]]:
    """Folds plus human-readable notes on skipped years."""
    folds: list[Fold] = []
    notes: list[str] = []
    for year in range(first_year, last_year + 1):
        s0 = quarter_index(f"{year}-Q1")
        test = [i for i, r in enumerate(panel.rows) if s0 <= r.q <= s0 + 3]
        if not test:
            continue
        train = [
            i
            for i, r in enumerate(panel.rows)
            if r.labels[horizon] is not None and r.q <= s0 - 1 - horizon
        ]
        events = sum(panel.rows[i].labels[horizon] or 0 for i in train)
        if events < min_train_events or len(train) - events < min_train_events:
            notes.append(
                f"{year}: skipped, training window has {events} events in {len(train)} rows"
            )
            continue
        folds.append(
            Fold(
                year=year,
                train=train,
                test=test,
                train_max_q=max(panel.rows[i].q for i in train),
                test_min_q=min(panel.rows[i].q for i in test),
            )
        )
    return folds, notes
