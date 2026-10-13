from fastapi import Request

from app.core.config import get_settings


def public_origin(request: Request) -> str:
    """Absolute origin for links people open outside the app (PDF footers, link previews).

    Prefers `PUBLIC_BASE_URL` (set it in production: behind a reverse proxy the request's own base
    URL is the internal address).
    """
    configured = (get_settings().public_base_url or "").rstrip("/")
    return configured or str(request.base_url).rstrip("/")
