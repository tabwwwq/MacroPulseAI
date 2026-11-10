"""Basic in-process rate limiting for compute endpoints (forecast backtests, scenario scoring).

A sliding one-minute window per client address. It protects a single API process from being kept
busy by one client; it is not a distributed quota. Behind the same-origin Next.js proxy every
browser shares the proxy's address, so the budget then applies to the web app as a whole.
"""

from __future__ import annotations

import math
import threading
import time
from collections import deque
from collections.abc import Callable

from fastapi import Request

from macropulse_api.errors import ApiError

MAX_TRACKED_CLIENTS = 10_000


class RateLimiter:
    def __init__(
        self,
        per_minute: int,
        *,
        window_s: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.per_minute = per_minute
        self.window_s = window_s
        self.clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str) -> float | None:
        """Record a request; return seconds until the next one is allowed when over the limit."""
        if self.per_minute <= 0:  # disabled
            return None
        now = self.clock()
        with self._lock:
            hits = self._hits.get(key)
            if hits is None:
                if len(self._hits) >= MAX_TRACKED_CLIENTS:
                    self._hits.clear()  # bounded memory; worst case one fresh window for everyone
                hits = self._hits[key] = deque()
            while hits and now - hits[0] >= self.window_s:
                hits.popleft()
            if len(hits) >= self.per_minute:
                return self.window_s - (now - hits[0])
            hits.append(now)
            return None


def compute_limit(request: Request) -> None:
    """FastAPI dependency for endpoints that run backtests or score models."""
    limiter: RateLimiter = request.app.state.compute_limiter
    key = request.client.host if request.client else "unknown"
    wait = limiter.hit(key)
    if wait is not None:
        retry = max(1, math.ceil(wait))
        raise ApiError(
            429,
            "rate_limited",
            f"Too many forecast or scenario requests; retry in {retry} s.",
            {"retry_after_s": retry, "limit_per_minute": limiter.per_minute},
            headers={"Retry-After": str(retry)},
        )
