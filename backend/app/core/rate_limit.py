"""Per-key sliding-window request limiter (in-process; one uvicorn worker is the deployed shape)."""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable

from fastapi import Request

from app.core.exceptions import TooManyRequestsError


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: float, clock: Callable[[], float] = time.monotonic):
        self._limit = limit
        self._window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}

    def hit(self, key: str) -> bool:
        """Record a request for `key`. Returns False (and records nothing) when over the limit."""
        now = self._clock()
        hits = self._hits.setdefault(key, deque())
        while hits and now - hits[0] >= self._window:
            hits.popleft()
        if len(hits) >= self._limit:
            return False
        hits.append(now)
        return True

    def reset(self) -> None:
        self._hits.clear()


def enforce_ip_limit(limiter: SlidingWindowLimiter, request: Request, detail: str) -> None:
    """Count a request against the caller's IP; 429 when over the limit."""
    ip = request.client.host if request.client else "unknown"
    if not limiter.hit(ip):
        raise TooManyRequestsError(detail)
