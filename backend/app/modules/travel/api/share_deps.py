"""Request dependencies for the public shared-plan endpoints: the link by code, and the friend by token."""

from __future__ import annotations

from datetime import timedelta

from fastapi import Depends, Header, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, GoneError, NotFoundError, UnauthorizedError
from app.core.short_codes import code_pattern
from app.core.timezone import as_utc, utc_now
from app.modules.travel import share_token
from app.modules.travel.models import TravelTripShare
from app.modules.travel.repository.shares import ShareRepository
from app.modules.travel.services.share_service import SHARE_CODE_LENGTH
from app.modules.travel.services.shared_plan_service import REMOVED, ContributorCtx

SHARE_CODE_PATTERN = code_pattern(SHARE_CODE_LENGTH)
LINK_NOT_FOUND = "This link doesn't exist. Check you have the whole link."
LINK_REVOKED = "This link has been turned off by the trip owner."
_SEEN_EVERY = timedelta(hours=1)

ShareCode = Path(pattern=SHARE_CODE_PATTERN)
ShareTokenHeader = Header(default=None, alias="X-Share-Token", max_length=2048)


async def share_by_code(code: str = ShareCode, db: AsyncSession = Depends(get_db)) -> TravelTripShare:
    """404 for an unknown code, 410 for a revoked one; neither says anything about the trip."""
    share = await ShareRepository(db).get_by_code(code)
    if share is None:
        raise NotFoundError(LINK_NOT_FOUND)
    if share.state == "revoked":
        raise GoneError(LINK_REVOKED)
    return share


async def require_contributor(
    share: TravelTripShare = Depends(share_by_code),
    token: str | None = ShareTokenHeader,
    db: AsyncSession = Depends(get_db),
) -> ContributorCtx:
    """The friend behind `X-Share-Token`, on this share only. Identity comes from the token, never the body."""
    if not token:
        raise UnauthorizedError(share_token.EXPIRED_MESSAGE)
    claims = share_token.decode(token)
    if claims.share_id != share.id:
        raise UnauthorizedError(share_token.EXPIRED_MESSAGE)
    contributor = await ShareRepository(db).get_contributor(share.id, claims.contributor_id)
    if contributor is None:
        raise UnauthorizedError(share_token.EXPIRED_MESSAGE)
    if contributor.removed_at is not None:
        raise ForbiddenError(REMOVED)
    now = utc_now()
    if contributor.last_seen_at is None or now - as_utc(contributor.last_seen_at) > _SEEN_EVERY:
        contributor.last_seen_at = now
    return ContributorCtx(share=share, contributor=contributor)
