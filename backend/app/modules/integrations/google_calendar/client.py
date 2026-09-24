"""Thin async adapter for the Google Calendar v3 events API. Never logs tokens."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://www.googleapis.com/calendar/v3"
TIMEOUT_SECONDS = 30.0
PAGE_SIZE = 250
MAX_PAGES = 40  # hard stop: 10k events in a 120-day window is far beyond normal use


class GoogleCalendarClientError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class GoogleCalendarClient:
    def __init__(self, access_token: str, calendar_id: str = "primary"):
        self._headers = {"Authorization": f"Bearer {access_token}"}
        self._base = f"{BASE_URL}/calendars/{quote(calendar_id, safe='')}/events"

    async def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                return await client.request(method, url, headers=self._headers, **kwargs)
        except httpx.HTTPError as exc:
            raise GoogleCalendarClientError(f"Google Calendar unreachable: {type(exc).__name__}") from exc

    async def list_events(self, time_min: datetime, time_max: datetime) -> tuple[list[dict], str | None]:
        """All single (expanded) events in the window. Returns (events, calendar_time_zone).

        Raises on any page failure so callers never act on a partial listing.
        """
        events: list[dict] = []
        tz: str | None = None
        page_token: str | None = None
        for _ in range(MAX_PAGES):
            params: dict[str, Any] = {
                "timeMin": time_min.isoformat(),
                "timeMax": time_max.isoformat(),
                "singleEvents": "true",
                "showDeleted": "false",
                "maxResults": PAGE_SIZE,
                "orderBy": "startTime",
            }
            if page_token:
                params["pageToken"] = page_token
            res = await self._request("GET", self._base, params=params)
            if res.status_code != 200:
                raise GoogleCalendarClientError(
                    f"List events failed with HTTP {res.status_code}", status_code=res.status_code
                )
            try:
                body = res.json()
            except ValueError as exc:
                raise GoogleCalendarClientError("List events returned invalid JSON") from exc
            tz = tz or body.get("timeZone")
            items = body.get("items") or []
            events.extend(i for i in items if isinstance(i, dict))
            page_token = body.get("nextPageToken")
            if not page_token:
                return events, tz
        raise GoogleCalendarClientError("Too many events in sync window")

    async def patch_event(self, event_id: str, body: dict[str, Any]) -> None:
        res = await self._request("PATCH", f"{self._base}/{quote(event_id, safe='')}", json=body)
        if res.status_code != 200:
            raise GoogleCalendarClientError(
                f"Update event failed with HTTP {res.status_code}", status_code=res.status_code
            )

    async def delete_event(self, event_id: str) -> None:
        res = await self._request("DELETE", f"{self._base}/{quote(event_id, safe='')}")
        # 404/410: already gone on Google — the desired end state.
        if res.status_code not in (200, 204, 404, 410):
            raise GoogleCalendarClientError(
                f"Delete event failed with HTTP {res.status_code}", status_code=res.status_code
            )
