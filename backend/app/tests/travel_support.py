"""Shared Travel test support: a fake Google Maps backend, its fixture, and auth helpers."""

from __future__ import annotations

import json
from unittest.mock import patch

import httpx
import pytest
from app.modules.travel.maps import gateway as maps_gateway
from app.modules.travel.maps import google as google_module


class FakeGoogle:
    """Routes Google Maps requests by path and records them. Tests set `status` to force an error."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.status: int | None = None

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.status:
            return httpx.Response(self.status, json={"error": "forced"})
        path = request.url.path
        if path.endswith("/geocode/json"):
            return httpx.Response(200, json=GEOCODE_BODY)
        if path.endswith("places:autocomplete"):
            return httpx.Response(200, json=AUTOCOMPLETE_BODY)
        if "/v1/places/" in path:
            return httpx.Response(200, json=PLACE_BODY)
        if path.endswith("directions/v2:computeRoutes"):
            return httpx.Response(200, json=ROUTES_BODY)
        if path.endswith("/elevation/json"):
            samples = int(request.url.params.get("samples", "2"))
            return httpx.Response(
                200, json={"status": "OK", "results": [{"elevation": 2000 + 10 * i} for i in range(samples)]}
            )
        return httpx.Response(404, json={})

    def bodies(self, suffix: str) -> list[dict]:
        return [json.loads(r.read()) for r in self.requests if r.url.path.endswith(suffix)]


GEOCODE_BODY = {
    "status": "OK",
    "results": [
        {
            "place_id": "ChIJhampta",
            "formatted_address": "Hampta Pass, Himachal Pradesh, India",
            "address_components": [
                {"long_name": "Hampta Pass", "types": ["natural_feature"]},
                {"long_name": "Himachal Pradesh", "types": ["administrative_area_level_1"]},
                {"long_name": "India", "types": ["country"]},
            ],
        }
    ],
}
AUTOCOMPLETE_BODY = {
    "suggestions": [
        {
            "placePrediction": {
                "placeId": "ChIJmanali",
                "structuredFormat": {
                    "mainText": {"text": "Manali"},
                    "secondaryText": {"text": "Himachal Pradesh, India"},
                },
            }
        }
    ]
}
PLACE_BODY = {
    "id": "ChIJmanali",
    "displayName": {"text": "Manali"},
    "formattedAddress": "Manali, Himachal Pradesh, India",
    "location": {"latitude": 32.2432, "longitude": 77.1892},
    "addressComponents": [{"longText": "India", "types": ["country"]}],
}
ROUTES_BODY = {
    "routes": [{"distanceMeters": 123456, "duration": "7200s", "polyline": {"encodedPolyline": "_p~iF~ps|U"}}]
}


@pytest.fixture
def isolated_uploads(tmp_path, monkeypatch):
    """Keep test uploads (GPX originals, photos) out of the real upload directory."""
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path / "uploads"))


@pytest.fixture
def google():
    fake = FakeGoogle()
    real = httpx.AsyncClient

    def factory(timeout: float) -> httpx.AsyncClient:
        return real(timeout=timeout, transport=httpx.MockTransport(fake))

    maps_gateway.reset_limiter()
    with patch.object(google_module, "_http_client", side_effect=factory):
        yield fake
    maps_gateway.reset_limiter()


async def auth(client, email: str) -> dict[str, str]:
    username = "usr_" + email.split("@")[0].replace(".", "").replace("_", "")[:26]
    await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": "password123", "display_name": "Traveller"},
    )
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def connect_google(client, headers) -> None:
    resp = await client.put(
        "/api/v1/integrations/google-maps/config", json={"api_key": "AIzaTESTKEY1234"}, headers=headers
    )
    assert resp.status_code == 200, resp.text
