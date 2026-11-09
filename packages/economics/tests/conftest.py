from __future__ import annotations

import os

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Live API checks are opt-in so CI stays deterministic and offline."""
    if os.environ.get("MACROPULSE_LIVE_TESTS") == "1":
        return
    skip = pytest.mark.skip(reason="live API check; set MACROPULSE_LIVE_TESTS=1 to run")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)
