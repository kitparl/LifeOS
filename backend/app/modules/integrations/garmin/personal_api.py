"""Thin async adapter for the Garmin Connect Personal API. Never logs keys or tokens.

Paths follow Garmin's official client (github.com/garmin/connect-personal-api-python). That client
needs Python 3.12+, and production runs 3.10, so the few calls LifeOS needs are made here with httpx.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://personal.connectapi.garmin.com"
TOKEN_PATH = "/personalapitoken-service/personal-api/personal-api-key/token"
TIMEOUT_SECONDS = 30.0
ACTIVITY_PAGE_SIZE = 50
MAX_ACTIVITY_PAGES = 40  # hard stop: 2000 activities in one sync window is far beyond normal use
# Garmin publishes no limits and may throttle without notice, so data calls are spaced out.
REQUEST_PAUSE_SECONDS = 0.25

JsonValue = dict[str, Any] | list[Any] | None


class GarminApiError(Exception):
    """A failed call. `auth` means the key or token was refused; `throttled` means Garmin is limiting requests."""

    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code

    @property
    def auth(self) -> bool:
        return self.status_code in (401, 403)

    @property
    def throttled(self) -> bool:
        return self.status_code == 429


def _http_client(timeout: float) -> httpx.AsyncClient:
    """Single construction point for Garmin HTTP clients (tests patch this seam)."""
    return httpx.AsyncClient(timeout=timeout)


async def _send(client: httpx.AsyncClient, method: str, path: str, **kwargs: Any) -> httpx.Response:
    try:
        response = await client.request(method, BASE_URL + path, **kwargs)
    except httpx.HTTPError as exc:
        raise GarminApiError(f"Garmin unreachable: {type(exc).__name__}") from exc
    if response.status_code != httpx.codes.OK:
        raise GarminApiError(f"Garmin returned HTTP {response.status_code}", status_code=response.status_code)
    return response


async def exchange_key(api_key: str) -> str:
    """Trade the personal API key for a bearer token (valid up to 24 hours; there is no refresh token)."""
    async with _http_client(TIMEOUT_SECONDS) as client:
        response = await _send(client, "POST", TOKEN_PATH, headers={"Authorization": f"ApiKey {api_key}", "Accept": "*/*"})
    token = response.text.strip()
    if not token:
        raise GarminApiError("Garmin returned an empty token")
    return token


class GarminPersonalApiClient:
    """Read-only calls with an already issued bearer token. Use as an async context manager."""

    def __init__(self, bearer_token: str):
        self._headers = {"Authorization": f"Bearer {bearer_token}", "Accept": "application/json"}
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> GarminPersonalApiClient:
        self._client = _http_client(TIMEOUT_SECONDS)
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def _get(self, path: str, **kwargs: Any) -> httpx.Response:
        assert self._client is not None, "use the client as an async context manager"
        await asyncio.sleep(REQUEST_PAUSE_SECONDS)
        headers = {**self._headers, **kwargs.pop("headers", {})}
        return await _send(self._client, "GET", path, headers=headers, **kwargs)

    async def _json(self, path: str, params: dict[str, Any] | None = None) -> JsonValue:
        response = await self._get(path, params=params)
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise GarminApiError("Garmin returned invalid JSON") from exc

    async def activity_ids(self, start: date, end: date) -> list[int]:
        """Ids of every activity that started in the inclusive date range."""
        ids: list[int] = []
        for page in range(MAX_ACTIVITY_PAGES):
            params = {
                "start": page * ACTIVITY_PAGE_SIZE,
                "limit": ACTIVITY_PAGE_SIZE,
                "startDate": start.isoformat(),
                "endDate": end.isoformat(),
            }
            items = await self._json("/activitylist-service/activities/search/activities", params)
            if not isinstance(items, list):
                raise GarminApiError("Garmin returned an unexpected activity list")
            for item in items:
                activity_id = item.get("activityId") if isinstance(item, dict) else None
                if isinstance(activity_id, int) and not isinstance(activity_id, bool) and activity_id > 0:
                    ids.append(activity_id)
            if len(items) < ACTIVITY_PAGE_SIZE:
                return ids
        raise GarminApiError("Too many activities in the sync window")

    async def download_activity(self, activity_id: int) -> bytes:
        """The original upload for an activity: a zip that holds the .FIT file."""
        response = await self._get(
            f"/download-service/files/activity/{int(activity_id)}",
            headers={"Accept": "application/zip, application/x-zip-compressed, application/octet-stream"},
        )
        if not response.content:
            raise GarminApiError("Garmin returned an empty activity file")
        return response.content

    async def daily_summaries(self, start: date, end: date) -> JsonValue:
        return await self._json(
            "/usersummary-service/v2/dailysummaries", {"startDate": start.isoformat(), "endDate": end.isoformat()}
        )

    async def daily_sleep(self, day: date) -> JsonValue:
        return await self._json("/sleep-service/sleep/dailySleep", {"date": day.isoformat()})

    async def daily_hrv(self, start: date, end: date) -> JsonValue:
        return await self._json(f"/hrv-service/hrv/daily/{start.isoformat()}/{end.isoformat()}")

    async def daily_spo2(self, day: date) -> JsonValue:
        return await self._json(f"/wellness-service/wellness/daily/spo2acclimation/{day.isoformat()}")

    async def weight_range(self, start: date, end: date) -> JsonValue:
        return await self._json(
            f"/weight-service/weight/range/{start.isoformat()}/{end.isoformat()}", {"includeAll": "true"}
        )
