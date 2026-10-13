"""The share-scoped token a friend gets on a trip link. The only module that knows its format.

It is deliberately unlike a LifeOS access token (requirements T-02): `type="share"`, its own
audience, no `sub`, and it travels in `X-Share-Token`, never `Authorization`. `get_current_user`
therefore rejects it, and it can never become a LifeOS session.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.timezone import utc_now

TOKEN_TYPE = "share"
TOKEN_AUDIENCE = "lifeos-share"
TOKEN_TTL = timedelta(hours=12)
EXPIRED_MESSAGE = "Your access to this plan has expired. Please continue again."


@dataclass(frozen=True)
class ShareClaims:
    share_id: str
    contributor_id: str


def issue(share_id: str, contributor_id: str, now: datetime | None = None) -> tuple[str, datetime]:
    settings = get_settings()
    expires_at = (now or utc_now()) + TOKEN_TTL
    claims = {"type": TOKEN_TYPE, "aud": TOKEN_AUDIENCE, "sid": share_id, "cid": contributor_id, "exp": expires_at}
    return jwt.encode(claims, settings.secret_key, algorithm=settings.algorithm), expires_at


def decode(token: str) -> ShareClaims:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm], audience=TOKEN_AUDIENCE)
    except JWTError:
        raise UnauthorizedError(EXPIRED_MESSAGE) from None
    share_id, contributor_id = payload.get("sid"), payload.get("cid")
    if payload.get("type") != TOKEN_TYPE or "sub" in payload or not share_id or not contributor_id:
        raise UnauthorizedError(EXPIRED_MESSAGE)
    return ShareClaims(share_id=str(share_id), contributor_id=str(contributor_id))
