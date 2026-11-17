"""Process-local record of FreeNewsAPI keys that are temporarily unusable.

When a key is rejected, rate limited or out of monthly quota the client parks it here and moves
on to the next key; a parked key is skipped until its `until` time. State is deliberately not
persisted: after a restart (or in another worker) the worst case is one extra failed request
before the key is parked again.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.core.timezone import utc_now

KeyState = Literal["ok", "rate_limited", "quota_exhausted", "invalid"]


@dataclass(frozen=True)
class ParkedKey:
    state: KeyState
    until: datetime


_parked: dict[str, ParkedKey] = {}


def fingerprint(key: str) -> str:
    """Stable, non-reversible id for a key (used as the state map key and as the id shown to the UI)."""
    return hashlib.sha256(key.encode()).hexdigest()[:12]


def park(key: str, state: KeyState, until: datetime) -> None:
    _parked[fingerprint(key)] = ParkedKey(state=state, until=until)


def clear(key: str) -> None:
    _parked.pop(fingerprint(key), None)


def parked(key: str) -> ParkedKey | None:
    """The key's active cooldown, or None when it is usable (expired cooldowns are dropped)."""
    entry = _parked.get(fingerprint(key))
    if entry is None:
        return None
    if entry.until <= utc_now():
        del _parked[fingerprint(key)]
        return None
    return entry


def reset() -> None:
    _parked.clear()
