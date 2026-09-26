"""Short-lived in-process TTL cache (never written to disk or the DB; not shared across processes)."""

from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Callable
from threading import Lock
from typing import Generic, TypeVar

V = TypeVar("V")


class TtlCache(Generic[V]):
    """TTL cache with an optional size bound (oldest entries are evicted first)."""

    def __init__(
        self,
        ttl_seconds: float,
        max_entries: int | None = None,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._ttl = ttl_seconds
        self._max = max_entries
        self._clock = clock
        self._items: OrderedDict[str, tuple[float, V]] = OrderedDict()
        self._lock = Lock()

    def get(self, key: str) -> V | None:
        with self._lock:
            entry = self._items.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if self._clock() >= expires_at:
                del self._items[key]
                return None
            return value

    def set(self, key: str, value: V, ttl: float | None = None) -> None:
        expires_at = self._clock() + (self._ttl if ttl is None else ttl)
        with self._lock:
            self._items.pop(key, None)
            self._items[key] = (expires_at, value)
            if self._max is not None:
                while len(self._items) > self._max:
                    self._items.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
