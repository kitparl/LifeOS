"""Short-lived in-process cache for FreeNewsAPI responses (never written to disk or the DB)."""

from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Callable
from typing import Generic, TypeVar

V = TypeVar("V")


class TtlCache(Generic[V]):
    """Bounded TTL cache. Oldest entries are evicted first. Not shared across processes."""

    def __init__(self, ttl_seconds: float, max_entries: int, clock: Callable[[], float] = time.monotonic):
        self._ttl = ttl_seconds
        self._max = max_entries
        self._clock = clock
        self._items: OrderedDict[str, tuple[float, V]] = OrderedDict()

    def get(self, key: str) -> V | None:
        entry = self._items.get(key)
        if entry is None:
            return None
        stored_at, value = entry
        if self._clock() - stored_at >= self._ttl:
            del self._items[key]
            return None
        return value

    def set(self, key: str, value: V) -> None:
        self._items.pop(key, None)
        self._items[key] = (self._clock(), value)
        while len(self._items) > self._max:
            self._items.popitem(last=False)

    def clear(self) -> None:
        self._items.clear()
