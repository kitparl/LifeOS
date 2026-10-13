"""The friend's side of a shared trip plan (public /t/<code> planner).

Friends are never LifeOS users: they are contributors on one share, identified by a Google account
or by a name plus a device secret, and act through a share-scoped token (see `share_token`).
Every write first checks the share is open (409 when locked); the request dependencies have already
turned unknown codes into 404, revoked links into 410 and removed friends into 403.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    PayloadTooLargeError,
    PreconditionFailedError,
    PreconditionRequiredError,
    UnauthorizedError,
)
from app.core.rate_limit import SlidingWindowLimiter
from app.core.short_codes import hash_secret, new_secret
from app.core.timezone import utc_now
from app.modules.auth.google_auth import GoogleIdentity, verify_google_id_claims
from app.modules.auth.models import User
from app.modules.notifications.schemas import NotificationCreate
from app.modules.notifications.service import NotificationService
from app.modules.travel import share_token
from app.modules.travel.maps.errors import MapsError, MapsUnavailable
from app.modules.travel.maps.gateway import MapsGateway
from app.modules.travel.maps.types import Feature, Sku, TravelMode
from app.modules.travel.maps_links import is_short_link, parse_maps_url, resolve_short_link
from app.modules.travel.models import TravelShareContributor, TravelShareVersion, TravelTripShare
from app.modules.travel.plan_document import copy_document, slim_leg
from app.modules.travel.repository.shares import ShareRepository
from app.modules.travel.repository.trips import TripRepository
from app.modules.travel.schemas.places import GeoLookupOut, SuggestionsOut
from app.modules.travel.schemas.plan_document import MAX_PLAN_BYTES, PlanDocument, RoadLeg
from app.modules.travel.schemas.shared import (
    ContributorMe,
    JoinOut,
    MyPlanOut,
    MyView,
    OwnerHint,
    PlanLimits,
    PublicPlanView,
    PublicTrip,
    ResolvedLink,
    RoadRouteOut,
    SessionOut,
)
from app.modules.travel.schemas.trips import MAX_ORDER_ITEMS, MAX_TRIP_DAYS
from app.modules.travel.services.export_service import ExportService
from app.modules.travel.services.lookup_service import LookupService
from app.modules.travel.services.share_service import owner_first_name

MAX_CONTRIBUTORS = 20
GUEST_LIMIT = "guest_limit"
LOCKED = "This plan is final now, so it can't be changed."
GOOGLE_REQUIRED = "Please continue with Google to make a plan."
NOT_INVITED = "This plan is only open to people the trip owner invited."
FULL = f"This plan already has {MAX_CONTRIBUTORS} people helping."
NO_PLAN = "Start your plan first."
STALE = "Your plan was updated on another device."
REMOVED = "The trip owner has removed you from this plan."

# Guests spend the owner's Google Maps quota: a daily cap per link and a short-window cap per
# visitor, on top of the owner's own monthly budget (requirements D-11).
_lookups_per_share = SlidingWindowLimiter(limit=150, window_seconds=24 * 3600)
_lookups_per_ip = SlidingWindowLimiter(limit=30, window_seconds=600)
# Road km: one Routes call per tap on a day, so the caps are lower than search.
_routes_per_share = SlidingWindowLimiter(limit=40, window_seconds=24 * 3600)
_routes_per_ip = SlidingWindowLimiter(limit=10, window_seconds=600)


@dataclass
class ContributorCtx:
    """The friend making a request, on the share their token belongs to (built by `require_contributor`)."""

    share: TravelTripShare
    contributor: TravelShareContributor


def reset_limiters() -> None:
    for limiter in (_lookups_per_share, _lookups_per_ip, _routes_per_share, _routes_per_ip):
        limiter.reset()


def _contributor_me(c: TravelShareContributor) -> ContributorMe:
    return ContributorMe(id=c.id, kind=c.kind, display_name=c.display_name)


def _my_plan(v: TravelShareVersion) -> MyPlanOut:
    return MyPlanOut(
        id=v.id,
        status=v.status,
        revision=v.revision,
        updated_at=v.updated_at,
        submitted_at=v.submitted_at,
        edited_since_sent=v.submitted_revision is not None and v.revision != v.submitted_revision,
        document=PlanDocument.model_validate(v.document),
    )


def _assert_open(share: TravelTripShare) -> None:
    if share.state != "open":
        raise ConflictError(LOCKED)


class SharedPlanService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ShareRepository(db)
        self.trips = TripRepository(db)
        self.lookup = LookupService(db)
        self.gateway = MapsGateway(db)
        self.export = ExportService(db)
        self.notifications = NotificationService(db)

    # ---- helpers ----------------------------------------------------------------------------

    async def _owner(self, share: TravelTripShare) -> User:
        return (await self.db.execute(select(User).where(User.id == share.user_id))).scalar_one()

    async def _document(self, share: TravelTripShare, version_id: str | None) -> PlanDocument:
        version = await self.repo.get_version(share.id, version_id) if version_id else None
        return PlanDocument.model_validate(version.document) if version else PlanDocument()

    async def _shown(self, share: TravelTripShare) -> tuple[PlanDocument, bool]:
        """What the link shows: the final plan once locked, else the Original. Returns (plan, is_final)."""
        is_final = share.state == "locked" and share.locked_version_id is not None
        return await self._document(share, share.locked_version_id if is_final else share.original_version_id), is_final

    async def _session(
        self, contributor: TravelShareContributor, share: TravelTripShare, *, new_device: bool
    ) -> JoinOut | SessionOut:
        token, expires_at = share_token.issue(share.id, contributor.id)
        plan = await self.repo.plan_for(share.id, contributor.id)
        common = {
            "contributor": _contributor_me(contributor),
            "plan": _my_plan(plan) if plan else None,
            "token": token,
            "expires_at": expires_at,
        }
        if not new_device:
            return SessionOut(**common)
        secret = new_secret()
        contributor.secret_hash = hash_secret(secret)  # one active device secret (requirements T-03)
        await self.repo.flush()
        return JoinOut(**common, device_secret=secret)

    async def _check_room(self, share: TravelTripShare) -> None:
        if await self.repo.count_contributors(share.id) >= MAX_CONTRIBUTORS:
            raise ConflictError(FULL)

    def _check_invited(self, share: TravelTripShare, email: str) -> None:
        if share.allowed_emails and email not in share.allowed_emails:
            raise ForbiddenError(NOT_INVITED)

    async def _is_owner(self, share: TravelTripShare, identity: GoogleIdentity) -> bool:
        return (await self._owner(share)).email.strip().lower() == identity.email

    async def _require_plan(self, ctx: ContributorCtx) -> TravelShareVersion:
        plan = await self.repo.plan_for(ctx.share.id, ctx.contributor.id)
        if plan is None:
            raise NotFoundError(NO_PLAN)
        return plan

    def _check_revision(self, plan: TravelShareVersion, if_match: int | None) -> None:
        if if_match is None:
            raise PreconditionRequiredError("Send the plan's revision in If-Match.")
        if if_match != plan.revision:
            raise PreconditionFailedError({"code": "stale", "revision": plan.revision, "message": STALE})

    def _write(self, plan: TravelShareVersion, doc: PlanDocument) -> None:
        if len(doc.model_dump_json()) > MAX_PLAN_BYTES:
            raise PayloadTooLargeError("This plan is too big to save.")
        plan.document = doc.model_dump(mode="json")
        plan.revision += 1
        plan.updated_at = utc_now()

    # ---- viewing ----------------------------------------------------------------------------

    async def view(self, share: TravelTripShare, viewer: User | None) -> PublicPlanView:
        trip = await self.trips.get(share.user_id, share.trip_id)
        plan, is_final = await self._shown(share)
        is_owner = viewer is not None and viewer.id == share.user_id
        return PublicPlanView(
            trip=PublicTrip(
                name=trip.name, description=trip.description, start_date=trip.start_date, end_date=trip.end_date
            ),
            owner_name=owner_first_name(await self._owner(share)),
            state="locked" if share.state == "locked" else "open",
            names_allowed=not share.require_google and not share.allowed_emails,
            google_enabled=bool(get_settings().google_client_id),
            is_final=is_final,
            viewer_is_owner=is_owner,
            manage_path=f"/travel/trips/{trip.id}?panel=share" if is_owner else None,
            plan=plan,
            limits=PlanLimits(max_days=MAX_TRIP_DAYS, max_stops=MAX_ORDER_ITEMS),
        )

    # ---- identity ---------------------------------------------------------------------------

    async def join_name(self, share: TravelTripShare, name: str) -> JoinOut:
        _assert_open(share)
        if share.require_google or share.allowed_emails:
            raise ForbiddenError(GOOGLE_REQUIRED)
        await self._check_room(share)
        contributor = TravelShareContributor(share_id=share.id, kind="name", display_name=name)
        await self.repo.add(contributor)
        return await self._session(contributor, share, new_device=True)

    async def join_google(self, share: TravelTripShare, credential: str) -> JoinOut | OwnerHint:
        _assert_open(share)
        identity = await verify_google_id_claims(credential)
        if await self._is_owner(share, identity):
            return OwnerHint()  # the owner manages the plan from LifeOS; nothing is created
        self._check_invited(share, identity.email)
        contributor = await self.repo.contributor_by_sub(share.id, identity.sub)
        if contributor is not None and contributor.removed_at is not None:
            raise ForbiddenError(REMOVED)
        if contributor is None:
            await self._check_room(share)
            contributor = TravelShareContributor(
                share_id=share.id,
                kind="google",
                display_name=identity.name[:40],
                google_sub=identity.sub,
                google_email=identity.email,
            )
            await self.repo.add(contributor)
        else:
            contributor.google_email = identity.email
        return await self._session(contributor, share, new_device=True)

    async def renew(self, share: TravelTripShare, device_secret: str) -> SessionOut:
        contributor = await self.repo.contributor_by_secret(share.id, hash_secret(device_secret))
        if contributor is None:
            raise UnauthorizedError("This device no longer has access to your plan.")
        if contributor.removed_at is not None:
            raise ForbiddenError(REMOVED)
        return await self._session(contributor, share, new_device=False)

    async def upgrade_google(self, ctx: ContributorCtx, credential: str) -> JoinOut:
        """A name-only friend links a Google account, keeping the same plan (requirements FR-F7)."""
        _assert_open(ctx.share)
        identity = await verify_google_id_claims(credential)
        if ctx.contributor.kind == "google":
            raise ConflictError("You're already signed in with Google.")
        if await self._is_owner(ctx.share, identity):
            raise ConflictError("That's the trip owner's account.")
        self._check_invited(ctx.share, identity.email)
        if await self.repo.contributor_by_sub(ctx.share.id, identity.sub) is not None:
            raise ConflictError("That Google account has already joined this plan.")
        ctx.contributor.kind = "google"
        ctx.contributor.google_sub = identity.sub
        ctx.contributor.google_email = identity.email
        return await self._session(ctx.contributor, ctx.share, new_device=True)

    async def me(self, ctx: ContributorCtx) -> MyView:
        plan = await self.repo.plan_for(ctx.share.id, ctx.contributor.id)
        return MyView(contributor=_contributor_me(ctx.contributor), plan=_my_plan(plan) if plan else None)

    # ---- the friend's plan ------------------------------------------------------------------

    async def start_plan(self, ctx: ContributorCtx) -> tuple[MyPlanOut, bool]:
        """The friend's own copy of the Original. Idempotent: returns (plan, created)."""
        _assert_open(ctx.share)
        existing = await self.repo.plan_for(ctx.share.id, ctx.contributor.id)
        if existing is not None:
            return _my_plan(existing), False
        original = await self._document(ctx.share, ctx.share.original_version_id)
        now = utc_now()
        plan = TravelShareVersion(
            share_id=ctx.share.id,
            kind="plan",
            contributor_id=ctx.contributor.id,
            label=f"{ctx.contributor.display_name}'s plan"[:80],
            status="draft",
            document=copy_document(original).model_dump(mode="json"),
            created_at=now,
            updated_at=now,
        )
        await self.repo.add(plan)
        return _my_plan(plan), True

    async def save_plan(self, ctx: ContributorCtx, if_match: int | None, doc: PlanDocument) -> MyPlanOut:
        _assert_open(ctx.share)
        plan = await self._require_plan(ctx)
        self._check_revision(plan, if_match)
        self._write(plan, doc)
        await self.repo.flush()
        return _my_plan(plan)

    async def reset_plan(self, ctx: ContributorCtx, if_match: int | None) -> MyPlanOut:
        _assert_open(ctx.share)
        plan = await self._require_plan(ctx)
        self._check_revision(plan, if_match)
        self._write(plan, copy_document(await self._document(ctx.share, ctx.share.original_version_id)))
        await self.repo.flush()
        return _my_plan(plan)

    async def submit(self, ctx: ContributorCtx, message: str | None) -> MyPlanOut:
        _assert_open(ctx.share)
        plan = await self._require_plan(ctx)
        plan.status = "submitted"
        plan.submitted_revision = plan.revision
        plan.submitted_at = utc_now()
        plan.message = message
        trip = await self.trips.get(ctx.share.user_id, ctx.share.trip_id)
        await self.notifications.create(
            ctx.share.user_id,
            NotificationCreate(
                message=f"{ctx.contributor.display_name} sent you a plan for {trip.name}",
                module="travel",
                entity_id=trip.id,
                route=f"/travel/trips/{trip.id}?panel=share",
            ),
        )
        await self.repo.flush()
        return _my_plan(plan)

    # ---- adding places ----------------------------------------------------------------------

    def _guest_lookup_allowed(self, share: TravelTripShare, client_key: str) -> bool:
        return _lookups_per_ip.hit(f"{share.id}:{client_key}") and _lookups_per_share.hit(share.id)

    async def autocomplete(
        self, ctx: ContributorCtx, client_key: str, query: str, session: str, bias: tuple[float, float] | None
    ) -> SuggestionsOut:
        _assert_open(ctx.share)
        if not self._guest_lookup_allowed(ctx.share, client_key):
            return SuggestionsOut(suggestions=[], fallback_reason=GUEST_LIMIT)
        return await self.lookup.autocomplete(ctx.share.user_id, query, session, bias, Feature.SHARED_SEARCH)

    async def place_details(
        self, ctx: ContributorCtx, client_key: str, external_place_id: str, session: str | None
    ) -> GeoLookupOut:
        _assert_open(ctx.share)
        if not self._guest_lookup_allowed(ctx.share, client_key):
            return GeoLookupOut(result=None, fallback_reason=GUEST_LIMIT)
        return await self.lookup.place_details(ctx.share.user_id, external_place_id, session, Feature.SHARED_SEARCH)

    async def resolve_link(self, ctx: ContributorCtx, url: str) -> ResolvedLink:
        _assert_open(ctx.share)
        parsed = await resolve_short_link(url) if is_short_link(url) else parse_maps_url(url)
        if parsed is None:
            return ResolvedLink()
        return ResolvedLink(name=parsed.name, lat=parsed.lat, lng=parsed.lng, google_place_id=parsed.google_place_id)

    # ---- road km and the PDF ----------------------------------------------------------------

    async def road_route(self, ctx: ContributorCtx, client_key: str, points: list[tuple[float, float]]) -> RoadRouteOut:
        """Road legs for one day's chain on the owner's key; the planner keeps straight-line estimates otherwise."""
        _assert_open(ctx.share)
        if not (_routes_per_ip.hit(f"{ctx.share.id}:{client_key}") and _routes_per_share.hit(ctx.share.id)):
            return RoadRouteOut(legs=[], fallback_reason=GUEST_LIMIT)
        try:
            result = await self.gateway.call(
                ctx.share.user_id,
                Sku.ROUTES,
                Feature.SHARED_ROUTE,
                lambda provider: provider.compute_route(points, TravelMode.DRIVING),
            )
        except MapsError as exc:
            return RoadRouteOut(legs=[], fallback_reason=exc.code)
        if len(result.legs) != len(points) - 1:
            return RoadRouteOut(legs=[], fallback_reason=MapsUnavailable.code)
        return RoadRouteOut(
            legs=[
                slim_leg(RoadLeg(distance_m=leg.distance_m, duration_s=leg.duration_s, polyline=leg.polyline))
                for leg in result.legs
            ]
        )

    async def shown_pdf(self, share: TravelTripShare) -> tuple[bytes, str]:
        plan, is_final = await self._shown(share)
        label = "final plan" if is_final else "plan"
        return await self.export.plan_pdf(share.user_id, share.trip_id, plan, label, public=True)

    async def my_plan_pdf(self, ctx: ContributorCtx) -> tuple[bytes, str]:
        plan = await self._require_plan(ctx)
        doc = PlanDocument.model_validate(plan.document)
        return await self.export.plan_pdf(ctx.share.user_id, ctx.share.trip_id, doc, plan.label, public=True)
