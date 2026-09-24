"""Verify Google Identity Services ID tokens (Sign in with Google).

The frontend sends the raw ID token; the email is taken only from the verified
token claims, never from client-supplied fields.
"""

import time

import httpx
from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError

GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("accounts.google.com", "https://accounts.google.com")
_JWKS_TTL_S = 3600.0

_jwks_cache: dict = {"keys": None, "fetched_at": 0.0}


async def _get_google_jwks() -> dict:
    now = time.monotonic()
    if _jwks_cache["keys"] is None or now - _jwks_cache["fetched_at"] > _JWKS_TTL_S:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(GOOGLE_JWKS_URL)
            resp.raise_for_status()
            _jwks_cache["keys"] = resp.json()
            _jwks_cache["fetched_at"] = now
    return _jwks_cache["keys"]


async def verify_google_id_token(credential: str) -> str:
    """Return the verified, lowercased email from a Google ID token.

    Raises UnauthorizedError if the token is invalid, not issued for this app,
    or the email is not verified by Google.
    """
    client_id = get_settings().google_client_id
    if not client_id:
        raise UnauthorizedError("Google sign-in is not configured")
    try:
        jwks = await _get_google_jwks()
        claims = jwt.decode(
            credential,
            jwks,
            algorithms=["RS256"],
            audience=client_id,
            issuer=GOOGLE_ISSUERS,
            options={"verify_at_hash": False},
        )
    except (JWTError, httpx.HTTPError):
        raise UnauthorizedError("Google sign-in failed. Please try again.") from None

    email = claims.get("email")
    if not email or claims.get("email_verified") is not True:
        raise UnauthorizedError("Google sign-in failed. Please try again.")
    return email.strip().lower()
