"""In-process TTL cache shared by the analytics dashboard service and AI insights."""

from app.core.cache import TtlCache

analytics_cache: TtlCache = TtlCache(ttl_seconds=60.0)
