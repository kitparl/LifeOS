"""`GET /t/{code}`: the app's index.html for the friend planner, with a link preview and strict headers.

WhatsApp and other link previewers do not run JavaScript, so the trip name must already be in the
HTML (requirements T-15, D-15). Only the trip name is used, escaped; an unknown or revoked code gets
a generic preview. Registered before the SPA catch-all in `main.py`.
"""

from __future__ import annotations

import re
from html import escape
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.public_url import public_origin
from app.core.rate_limit import SlidingWindowLimiter, enforce_ip_limit
from app.modules.travel.repository.shares import ShareRepository
from app.modules.travel.repository.trips import TripRepository

INDEX_HTML = Path(__file__).resolve().parents[3] / "static" / "index.html"
OG_IMAGE_PATH = "/planner/og-image.png"
GENERIC_TITLE = "A trip plan"
DESCRIPTION = "Help plan this trip. Add places, times and ideas, then send your plan."
_CODE = re.compile(r"^[23456789abcdefghijkmnopqrstuvwxyz]{8}$")
# Angular's critical-CSS loader flips the stylesheet in with an inline `onload`, which the CSP below
# forbids; a plain stylesheet link is used instead (the page is small, so render-blocking is fine).
_DEFERRED_STYLES = re.compile(r"""\s+media="print"\s+onload="this\.media='all'\"""")

_limiter = SlidingWindowLimiter(limit=120, window_seconds=600)

router = APIRouter()


def reset_limiter() -> None:
    _limiter.reset()


def _tile_hosts() -> str:
    hosts = {"https://tile.openstreetmap.org", "https://*.tile.openstreetmap.org"}
    configured = urlparse(get_settings().travel_map_tile_url.replace("{s}", "a"))
    if configured.scheme == "https" and configured.hostname:
        hosts.add(f"https://{configured.hostname}")
    return " ".join(sorted(hosts))


def content_security_policy() -> str:
    google = "https://accounts.google.com"
    return "; ".join(
        [
            "default-src 'self'",
            f"script-src 'self' {google}/gsi/client",
            f"frame-src {google}",
            f"connect-src 'self' {google}",
            f"img-src 'self' data: blob: {_tile_hosts()}",
            # Angular injects component styles at runtime, so inline styles are required (documented exception).
            f"style-src 'self' 'unsafe-inline' {google}/gsi/style https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]
    )


def _headers() -> dict[str, str]:
    headers = {
        "Content-Security-Policy": content_security_policy(),
        "Referrer-Policy": "no-referrer",
        "X-Robots-Tag": "noindex, nofollow",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Cache-Control": "no-cache, no-store, must-revalidate",
    }
    if get_settings().is_production:
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return headers


def render_page(index_html: str, title: str, origin: str) -> str:
    safe_title = escape(title, quote=True)
    tags = "\n".join(
        [
            f'  <meta property="og:title" content="{safe_title}">',
            f'  <meta property="og:description" content="{escape(DESCRIPTION, quote=True)}">',
            f'  <meta property="og:image" content="{escape(origin + OG_IMAGE_PATH, quote=True)}">',
            '  <meta property="og:image:width" content="1200">',
            '  <meta property="og:image:height" content="630">',
            '  <meta property="og:type" content="website">',
            '  <meta name="twitter:card" content="summary_large_image">',
            f'  <meta name="description" content="{escape(DESCRIPTION, quote=True)}">',
            '  <meta name="robots" content="noindex, nofollow">',
            '  <meta name="referrer" content="no-referrer">',
        ]
    )
    page = re.sub(r"<title>.*?</title>", lambda _: f"<title>{safe_title}</title>", index_html, count=1, flags=re.S)
    page = _DEFERRED_STYLES.sub("", page)
    return page.replace("</head>", f"{tags}\n</head>", 1)


async def _trip_name(db: AsyncSession, code: str) -> str | None:
    """The trip name for an active link; None for unknown, malformed or revoked codes."""
    if not _CODE.match(code):
        return None
    share = await ShareRepository(db).get_by_code(code)
    if share is None or share.state == "revoked":
        return None
    trip = await TripRepository(db).get(share.user_id, share.trip_id)
    return trip.name if trip else None


@router.get("/t/{code}", response_class=HTMLResponse, include_in_schema=False)
async def shared_plan_page(code: str, request: Request, db: AsyncSession = Depends(get_db)) -> HTMLResponse:
    enforce_ip_limit(_limiter, request, "Too many requests. Please wait a minute and try again.")
    if not INDEX_HTML.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    name = await _trip_name(db, code)
    html = render_page(INDEX_HTML.read_text(encoding="utf-8"), name or GENERIC_TITLE, public_origin(request))
    return HTMLResponse(html, headers=_headers())
