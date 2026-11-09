"""Polite, resilient HTTP access to official APIs: timeouts, retries with backoff, Retry-After,
per-host throttling. TLS is always verified (httpx uses the certifi CA bundle — see ADR-0008)."""

from __future__ import annotations

import time
from collections.abc import Callable
from urllib.parse import urlsplit

import httpx

from macropulse_economics.connectors.base import ConnectorError

USER_AGENT = "MacroPulse/0.3 (+https://github.com/tabwwwq/MacroPulseAI)"
RETRY_STATUS = {429, 500, 502, 503, 504}
MIN_INTERVAL_S = 0.5  # minimum spacing between requests to the same host


def make_client(transport: httpx.BaseTransport | None = None) -> httpx.Client:
    return httpx.Client(
        timeout=httpx.Timeout(45.0, connect=10.0),
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
        transport=transport,
    )


class Fetcher:
    """GET with retries. `sleep` is injectable so tests run instantly."""

    def __init__(
        self,
        client: httpx.Client,
        retries: int = 3,
        backoff_s: float = 1.5,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.client = client
        self.retries = retries
        self.backoff_s = backoff_s
        self.sleep = sleep
        self._last_call: dict[str, float] = {}

    def _throttle(self, url: str) -> None:
        host = urlsplit(url).netloc
        last = self._last_call.get(host)
        if last is not None:
            wait = MIN_INTERVAL_S - (time.monotonic() - last)
            if wait > 0:
                self.sleep(wait)
        self._last_call[host] = time.monotonic()

    def get(self, url: str, params: dict[str, str] | None = None) -> httpx.Response:
        last_error = "no attempt made"
        for attempt in range(self.retries + 1):
            self._throttle(url)
            try:
                response = self.client.get(url, params=params)
            except httpx.TransportError as exc:
                last_error = f"{type(exc).__name__}"
            else:
                if response.status_code < 400:
                    return response
                last_error = f"HTTP {response.status_code}"
                if response.status_code not in RETRY_STATUS:
                    break  # 4xx other than 429: the request itself is wrong; retrying won't help
                retry_after = response.headers.get("Retry-After", "")
                if retry_after.isdigit() and attempt < self.retries:
                    self.sleep(min(float(retry_after), 60.0))
                    continue
            if attempt < self.retries:
                self.sleep(self.backoff_s * (2**attempt))
        host = urlsplit(url).netloc
        raise ConnectorError(
            f"{host}: request failed after {self.retries + 1} attempt(s) ({last_error})"
        )
