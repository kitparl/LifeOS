"""Process-local record of FreeNewsAPI keys that are temporarily unusable.

When a key is rejected, rate limited or out of monthly quota the client parks it here and moves
on to the next key; a parked key is skipped until its `until` time. State is deliberately not
persisted: after a restart (or in another worker) the worst case is one extra failed request
before the key is parked again.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from app.core.timezone import utc_now

KeyState = Literal["ok", "rate_limited", "quota_exhausted", "invalid"]


@dataclass(frozen=True)
class ParkedKey:
    state: KeyState
    until: datetime


@dataclass(frozen=True)
class KeyQuota:
    """Last `X-Quota-Remaining` / `X-Quota-Limit` reading the vendor returned for a key."""

    remaining: int
    limit: int
    observed_at: datetime


_parked: dict[str, ParkedKey] = {}
_quotas: dict[str, KeyQuota] = {}


def month_start(now: datetime) -> datetime:
    return datetime(now.year, now.month, 1, tzinfo=timezone.utc)


def next_quota_renewal(now: datetime) -> datetime:
    """The monthly allowance renews on the 1st at 00:00 UTC."""
    year, month = (now.year + 1, 1) if now.month == 12 else (now.year, now.month + 1)
    return datetime(year, month, 1, tzinfo=timezone.utc)


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


def record_quota(key: str, remaining: int, limit: int) -> None:
    _quotas[fingerprint(key)] = KeyQuota(remaining=remaining, limit=limit, observed_at=utc_now())


def quota(key: str) -> KeyQuota | None:
    """The last quota reading, or None when unknown. A reading from an earlier month is stale (the quota renewed)."""
    reading = _quotas.get(fingerprint(key))
    if reading is None or reading.observed_at < month_start(utc_now()):
        return None
    return reading


def reset() -> None:
    _parked.clear()
    _quotas.clear()
