"""Google OAuth 2.0 authorization-code flow for Calendar access (httpx, no Google SDK).

Deliberately separate from Sign-in-with-Google (GIS ID tokens in ``auth/google_auth.py``):
this flow requests Calendar scopes and a refresh token. Never logs tokens or codes.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from jose import JWTError, jwt

from app.core.config import get_settings
from app.modules.integrations.google_calendar.config import (
    SCOPE_READONLY,
    SCOPE_READWRITE,
    SYNC_DIRECTIONS,
)

logger = logging.getLogger(__name__)

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
STATE_PURPOSE = "gcal_oauth"
STATE_TTL = timedelta(minutes=10)
TIMEOUT_SECONDS = 20.0


class GoogleOAuthError(Exception):
    """Raised for any OAuth failure. Message is safe to log (no secrets)."""


def is_configured() -> bool:
    s = get_settings()
    return bool(s.google_client_id and s.google_client_secret and s.google_calendar_redirect_uri)


def scope_for(direction: str) -> str:
    # Least privilege: write scope only when the user asks for two-way.
    return SCOPE_READWRITE if direction == "two_way" else SCOPE_READONLY


def create_state(user_id: str, direction: str) -> str:
    s = get_settings()
    payload = {
        "sub": user_id,
        "purpose": STATE_PURPOSE,
        "mode": direction,
        "exp": datetime.now(UTC) + STATE_TTL,
    }
    return jwt.encode(payload, s.secret_key, algorithm=s.algorithm)


def verify_state(state: str, user_id: str) -> str:
    """Validate signature, expiry, purpose and user binding. Returns the requested mode."""
    s = get_settings()
    try:
        payload = jwt.decode(state, s.secret_key, algorithms=[s.algorithm])
    except JWTError as exc:
        raise GoogleOAuthError("Invalid or expired OAuth state") from exc
    if payload.get("purpose") != STATE_PURPOSE or payload.get("sub") != user_id:
        raise GoogleOAuthError("OAuth state does not match this user")
    mode = payload.get("mode")
    if mode not in SYNC_DIRECTIONS:
        raise GoogleOAuthError("Invalid OAuth state")
    return str(mode)


def build_auth_url(user_id: str, direction: str) -> str:
    s = get_settings()
    params = {
        "client_id": s.google_client_id,
        "redirect_uri": s.google_calendar_redirect_uri,
        "response_type": "code",
        "scope": scope_for(direction),
        "access_type": "offline",
        # Force consent so Google always returns a refresh token (also on scope upgrade).
        "prompt": "consent",
        "include_granted_scopes": "false",
        "state": create_state(user_id, direction),
    }
    return f"{AUTH_URL}?{urlencode(params)}"


async def _post_token(data: dict[str, str]) -> dict:
    s = get_settings()
    body = {"client_id": s.google_client_id, "client_secret": s.google_client_secret, **data}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            res = await client.post(TOKEN_URL, data=body)
    except httpx.HTTPError as exc:
        raise GoogleOAuthError(f"Token endpoint unreachable: {type(exc).__name__}") from exc
    if res.status_code != 200:
        # Google returns {"error": "invalid_grant", ...}; log only the error code.
        try:
            err = res.json().get("error", "unknown")
        except ValueError:
            err = "unknown"
        raise GoogleOAuthError(f"Token endpoint returned {res.status_code} ({err})")
    try:
        payload = res.json()
    except ValueError as exc:
        raise GoogleOAuthError("Token endpoint returned invalid JSON") from exc
    if not isinstance(payload, dict) or not payload.get("access_token"):
        raise GoogleOAuthError("Token endpoint response missing access_token")
    return payload


async def exchange_code(code: str) -> tuple[str, str]:
    """Exchange an authorization code. Returns (refresh_token, granted_scope)."""
    payload = await _post_token(
        {
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": get_settings().google_calendar_redirect_uri,
        }
    )
    refresh = payload.get("refresh_token")
    if not refresh:
        raise GoogleOAuthError("Google did not return a refresh token")
    return str(refresh), str(payload.get("scope") or "")


async def refresh_access_token(refresh_token: str) -> str:
    payload = await _post_token({"refresh_token": refresh_token, "grant_type": "refresh_token"})
    return str(payload["access_token"])


async def revoke(token: str) -> None:
    """Best effort: failures are logged and ignored (local cleanup proceeds regardless)."""
    if not token:
        return
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            res = await client.post(REVOKE_URL, data={"token": token})
        if res.status_code not in (200, 400):  # 400 = already revoked/invalid
            logger.warning("Google token revoke returned %s", res.status_code)
    except httpx.HTTPError as exc:
        logger.warning("Google token revoke failed: %s", type(exc).__name__)
