"""Shared Asia/Kolkata (IST) time helpers.

Several modules independently inline ``ZoneInfo("Asia/Kolkata")`` for "today" boundaries
(``routines/service.py``, ``integrations/scheduling/scheduler.py``). This is the first
module whose correctness depends on a *fixed* (non-user-configurable) IST boundary, so it
gets a shared helper instead of another inline copy.
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def ist_now() -> datetime:
    return datetime.now(IST)


def ist_today() -> date:
    return ist_now().date()
