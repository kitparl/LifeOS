"""News proxy rate-limit key (the limiter itself is ``app.core.rate_limit.SlidingWindowLimiter``)."""

from __future__ import annotations

import hashlib


def proxy_limit_key(user_id: str | None, client_ip: str | None) -> str:
    """Signed-in callers are limited per user; anonymous (Explore) callers per client IP, hashed so raw IPs aren't held."""
    if user_id is not None:
        return user_id
    digest = hashlib.sha256((client_ip or "unknown").encode()).hexdigest()[:32]
    return f"guest:{digest}"
