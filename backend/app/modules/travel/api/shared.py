"""Public endpoints of the friend planner at /t/<code>. No LifeOS login: friends use `X-Share-Token`.

Every endpoint is rate-limited by visitor (hashed IP) and, where a script could flood a link, by
code or by friend too (requirements T-12). Responses are never cached.
"""

from fastapi import APIRouter, Depends, Header, Path, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_optional_user
from app.core.exceptions import PayloadTooLargeError, TooManyRequestsError
from app.core.rate_limit import SlidingWindowLimiter
from app.modules.auth.models import User
from app.modules.news.rate_limit import proxy_limit_key
from app.modules.travel.api.share_deps import require_contributor, share_by_code
from app.modules.travel.models import TravelTripShare
from app.modules.travel.schemas.places import GeoLookupOut, SuggestionsOut
from app.modules.travel.schemas.plan_document import MAX_PLAN_BYTES, PlanDocument
from app.modules.travel.schemas.shared import (
    GoogleCredential,
    JoinName,
    JoinOut,
    MyPlanOut,
    MyView,
    OwnerHint,
    PublicPlanView,
    ResolvedLink,
    RoadRouteIn,
    RoadRouteOut,
    SessionOut,
    SessionRenew,
    SubmitIn,
)
from app.modules.travel.services.shared_plan_service import ContributorCtx, SharedPlanService

SLOW_DOWN = "Too many requests. Please wait a minute and try again."
_SESSION = r"^[A-Za-z0-9-]{8,64}$"
_TEN_MIN = 600.0

_view_ip = SlidingWindowLimiter(limit=120, window_seconds=_TEN_MIN)
_join_ip = SlidingWindowLimiter(limit=10, window_seconds=_TEN_MIN)
_join_code = SlidingWindowLimiter(limit=40, window_seconds=24 * 3600)
_session_ip = SlidingWindowLimiter(limit=30, window_seconds=_TEN_MIN)
_write_friend = SlidingWindowLimiter(limit=120, window_seconds=_TEN_MIN)
_write_code = SlidingWindowLimiter(limit=600, window_seconds=_TEN_MIN)
_submit_friend = SlidingWindowLimiter(limit=10, window_seconds=_TEN_MIN)
_resolve_ip = SlidingWindowLimiter(limit=20, window_seconds=_TEN_MIN)
# A PDF fetches map tiles and renders every day, so it is the most expensive read.
_pdf_ip = SlidingWindowLimiter(limit=6, window_seconds=_TEN_MIN)
_pdf_code = SlidingWindowLimiter(limit=60, window_seconds=24 * 3600)
_LIMITERS = (
    _view_ip,
    _join_ip,
    _join_code,
    _session_ip,
    _write_friend,
    _write_code,
    _submit_friend,
    _resolve_ip,
    _pdf_ip,
    _pdf_code,
)


def reset_limiters() -> None:
    """Forget rate-limit history (tests)."""
    for limiter in _LIMITERS:
        limiter.reset()


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Robots-Tag"] = "noindex"


router = APIRouter(prefix="/shared/{code}", dependencies=[Depends(_no_store)])


def _visitor(request: Request) -> str:
    return proxy_limit_key(None, request.client.host if request.client else None)


def _hit(limiter: SlidingWindowLimiter, key: str) -> None:
    if not limiter.hit(key):
        raise TooManyRequestsError(SLOW_DOWN)


def _write_limits(ctx: ContributorCtx) -> None:
    _hit(_write_friend, ctx.contributor.id)
    _hit(_write_code, ctx.share.id)


def _if_match(value: str | None) -> int | None:
    """`If-Match: "3"` (or `3`) -> 3. Anything else counts as missing (428)."""
    if value is None:
        return None
    cleaned = value.strip().removeprefix("W/").strip('"')
    return int(cleaned) if cleaned.isdigit() else None


def _body_size(request: Request) -> None:
    """Reject an oversized plan before it is parsed (the service re-checks the parsed size)."""
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > MAX_PLAN_BYTES:
        raise PayloadTooLargeError("This plan is too big to save.")


def _pdf_limits(request: Request, share: TravelTripShare) -> None:
    _hit(_pdf_ip, _visitor(request))
    _hit(_pdf_code, share.id)


def _pdf_response(pdf: bytes, name: str) -> Response:
    # A returned Response skips the router's header dependency, so the same headers are set here.
    response = Response(pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{name}"'})
    _no_store(response)
    return response


IfMatch = Header(default=None, alias="If-Match", max_length=32)


@router.get("", response_model=PublicPlanView)
async def view_plan(
    request: Request,
    share: TravelTripShare = Depends(share_by_code),
    viewer: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    _hit(_view_ip, _visitor(request))
    return await SharedPlanService(db).view(share, viewer)


@router.post("/join/name", response_model=JoinOut, status_code=status.HTTP_201_CREATED)
async def join_with_name(
    data: JoinName,
    request: Request,
    share: TravelTripShare = Depends(share_by_code),
    db: AsyncSession = Depends(get_db),
):
    _hit(_join_ip, _visitor(request))
    _hit(_join_code, share.id)
    return await SharedPlanService(db).join_name(share, data.name)


@router.post("/join/google", response_model=JoinOut | OwnerHint, status_code=status.HTTP_201_CREATED)
async def join_with_google(
    data: GoogleCredential,
    request: Request,
    share: TravelTripShare = Depends(share_by_code),
    db: AsyncSession = Depends(get_db),
):
    _hit(_join_ip, _visitor(request))
    _hit(_join_code, share.id)
    return await SharedPlanService(db).join_google(share, data.credential)


@router.post("/session", response_model=SessionOut)
async def renew_session(
    data: SessionRenew,
    request: Request,
    share: TravelTripShare = Depends(share_by_code),
    db: AsyncSession = Depends(get_db),
):
    _hit(_session_ip, _visitor(request))
    return await SharedPlanService(db).renew(share, data.device_secret)


@router.post("/me/upgrade-google", response_model=JoinOut)
async def upgrade_to_google(
    data: GoogleCredential, ctx: ContributorCtx = Depends(require_contributor), db: AsyncSession = Depends(get_db)
):
    _write_limits(ctx)
    return await SharedPlanService(db).upgrade_google(ctx, data.credential)


@router.get("/me", response_model=MyView)
async def my_view(ctx: ContributorCtx = Depends(require_contributor), db: AsyncSession = Depends(get_db)):
    return await SharedPlanService(db).me(ctx)


@router.post("/me/plan", response_model=MyPlanOut)
async def start_my_plan(
    response: Response, ctx: ContributorCtx = Depends(require_contributor), db: AsyncSession = Depends(get_db)
):
    _write_limits(ctx)
    plan, created = await SharedPlanService(db).start_plan(ctx)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    response.headers["ETag"] = f'"{plan.revision}"'
    return plan


@router.put("/me/plan", response_model=MyPlanOut, dependencies=[Depends(_body_size)])
async def save_my_plan(
    doc: PlanDocument,
    response: Response,
    if_match: str | None = IfMatch,
    ctx: ContributorCtx = Depends(require_contributor),
    db: AsyncSession = Depends(get_db),
):
    _write_limits(ctx)
    plan = await SharedPlanService(db).save_plan(ctx, _if_match(if_match), doc)
    response.headers["ETag"] = f'"{plan.revision}"'
    return plan


@router.post("/me/plan/reset", response_model=MyPlanOut)
async def reset_my_plan(
    response: Response,
    if_match: str | None = IfMatch,
    ctx: ContributorCtx = Depends(require_contributor),
    db: AsyncSession = Depends(get_db),
):
    _write_limits(ctx)
    plan = await SharedPlanService(db).reset_plan(ctx, _if_match(if_match))
    response.headers["ETag"] = f'"{plan.revision}"'
    return plan


@router.post("/me/plan/submit", response_model=MyPlanOut)
async def submit_my_plan(
    data: SubmitIn, ctx: ContributorCtx = Depends(require_contributor), db: AsyncSession = Depends(get_db)
):
    _hit(_submit_friend, ctx.contributor.id)
    return await SharedPlanService(db).submit(ctx, data.message)


@router.get("/maps/autocomplete", response_model=SuggestionsOut)
async def guest_autocomplete(
    request: Request,
    q: str = Query(min_length=1, max_length=100),
    session: str = Query(pattern=_SESSION),
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    ctx: ContributorCtx = Depends(require_contributor),
    db: AsyncSession = Depends(get_db),
):
    bias = (lat, lng) if lat is not None and lng is not None else None
    return await SharedPlanService(db).autocomplete(ctx, _visitor(request), q, session, bias)


@router.get("/maps/place/{external_place_id}", response_model=GeoLookupOut)
async def guest_place_details(
    request: Request,
    external_place_id: str = Path(max_length=255, pattern=r"^[A-Za-z0-9_\-:.]+$"),
    session: str | None = Query(default=None, pattern=_SESSION),
    ctx: ContributorCtx = Depends(require_contributor),
    db: AsyncSession = Depends(get_db),
):
    return await SharedPlanService(db).place_details(ctx, _visitor(request), external_place_id, session)


@router.get("/resolve-link", response_model=ResolvedLink)
async def resolve_link(
    request: Request,
    url: str = Query(min_length=8, max_length=2048),
    ctx: ContributorCtx = Depends(require_contributor),
    db: AsyncSession = Depends(get_db),
):
    _hit(_resolve_ip, _visitor(request))
    return await SharedPlanService(db).resolve_link(ctx, url)


@router.post("/route", response_model=RoadRouteOut)
async def road_route(
    data: RoadRouteIn,
    request: Request,
    ctx: ContributorCtx = Depends(require_contributor),
    db: AsyncSession = Depends(get_db),
):
    return await SharedPlanService(db).road_route(ctx, _visitor(request), data.points)


@router.get("/pdf", response_class=Response)
async def shown_plan_pdf(
    request: Request, share: TravelTripShare = Depends(share_by_code), db: AsyncSession = Depends(get_db)
):
    """The plan the link shows (the final plan once locked) as the PDF guide. Anyone with the link."""
    _pdf_limits(request, share)
    return _pdf_response(*await SharedPlanService(db).shown_pdf(share))


@router.get("/me/plan/pdf", response_class=Response)
async def my_plan_pdf(
    request: Request, ctx: ContributorCtx = Depends(require_contributor), db: AsyncSession = Depends(get_db)
):
    _pdf_limits(request, ctx.share)
    return _pdf_response(*await SharedPlanService(db).my_plan_pdf(ctx))
