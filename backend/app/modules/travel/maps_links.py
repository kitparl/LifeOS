"""Reading a pasted Google Maps link: the place's name and coordinates, without calling any Google API.

Full links carry the coordinates in the URL. Links shared from the Google Maps phone app are short
links (`maps.app.goo.gl/...`) that only reveal them after a redirect, so the backend follows those
redirects (requirements D-12, T-14) under tight rules against SSRF: https only, a fixed list of
Google hosts on every hop, at most 5 hops, a short timeout, and the response body is never read.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, unquote_plus, urljoin, urlparse

import httpx

MAX_HOPS = 5
TIMEOUT_SECONDS = 3.0
SHORT_HOSTS = frozenset({"maps.app.goo.gl", "goo.gl"})
_GOOGLE_HOST = re.compile(r"^(www\.|maps\.)?google\.[a-z]{2,3}(\.[a-z]{2})?$")
_CONSENT_HOST = "consent.google.com"
_PRECISE = re.compile(r"!3d(-?\d{1,2}(?:\.\d+)?)!4d(-?\d{1,3}(?:\.\d+)?)")
_VIEWPORT = re.compile(r"@(-?\d{1,2}(?:\.\d+)?),(-?\d{1,3}(?:\.\d+)?)")
_LAT_LNG = re.compile(r"^\s*(-?\d{1,2}(?:\.\d+)?)\s*,\s*(-?\d{1,3}(?:\.\d+)?)\s*$")
_PLACE_ID = re.compile(r"^[A-Za-z0-9_\-:.]{1,255}$")


@dataclass(frozen=True)
class ParsedLink:
    name: str | None = None
    lat: float | None = None
    lng: float | None = None
    google_place_id: str | None = None


def _http_client(timeout: float) -> httpx.AsyncClient:
    """Single construction point (tests patch this seam). Redirects are followed by hand, never by httpx."""
    return httpx.AsyncClient(timeout=timeout, follow_redirects=False)


def _is_google_maps_host(host: str) -> bool:
    return bool(_GOOGLE_HOST.match(host)) or host in SHORT_HOSTS


def is_short_link(url: str) -> bool:
    parts = urlparse(url.strip())
    host = (parts.hostname or "").lower()
    if parts.scheme != "https":
        return False
    return host == "maps.app.goo.gl" or (host == "goo.gl" and parts.path.startswith("/maps"))


def _coords(lat: str, lng: str) -> tuple[float, float] | None:
    la, ln = float(lat), float(lng)
    return (la, ln) if -90 <= la <= 90 and -180 <= ln <= 180 else None


def parse_maps_url(url: str) -> ParsedLink | None:
    """Name / coordinates / place id from a full Google Maps URL, or None when it holds none of them."""
    parts = urlparse(url.strip())
    host = (parts.hostname or "").lower()
    if parts.scheme not in ("http", "https") or not _GOOGLE_HOST.match(host):
        return None
    query = parse_qs(parts.query)
    full = unquote_plus(parts.path) + "?" + unquote_plus(parts.query)

    point = None
    for pattern in (_PRECISE, _VIEWPORT):
        match = pattern.search(full)
        if match and (point := _coords(*match.groups())):
            break
    name = None
    for key in ("q", "query", "destination", "ll"):
        value = (query.get(key) or [""])[0].strip()
        if not value:
            continue
        match = _LAT_LNG.match(value)
        if match:
            point = point or _coords(*match.groups())
        elif name is None:
            name = value[:200]
    place_match = re.search(r"/place/([^/@]+)", parts.path)
    if place_match:
        name = unquote_plus(place_match.group(1)).strip()[:200] or name
    place_id = (query.get("query_place_id") or query.get("place_id") or [None])[0]
    if place_id and not _PLACE_ID.match(place_id):
        place_id = None

    if point is None and name is None and place_id is None:
        return None
    return ParsedLink(
        name=name,
        lat=point[0] if point else None,
        lng=point[1] if point else None,
        google_place_id=place_id,
    )


async def resolve_short_link(url: str) -> ParsedLink | None:
    """Follow a Google Maps short link to its full URL and parse that. None on any problem (fails closed)."""
    if not is_short_link(url):
        return None
    current = url.strip()
    try:
        async with _http_client(TIMEOUT_SECONDS) as client:
            for _ in range(MAX_HOPS):
                parts = urlparse(current)
                host = (parts.hostname or "").lower()
                if host == _CONSENT_HOST:
                    # EU consent interstitial: the real destination is in `continue`; never fetch the page.
                    current = (parse_qs(parts.query).get("continue") or [""])[0]
                    continue
                if parts.scheme != "https" or not _is_google_maps_host(host):
                    return None
                if host not in SHORT_HOSTS:
                    return parse_maps_url(current)
                async with client.stream("GET", current) as response:
                    location = response.headers.get("location")
                    if not response.is_redirect or not location:
                        return None
                current = urljoin(current, location)
    except (httpx.HTTPError, ValueError):
        return None
    return None
