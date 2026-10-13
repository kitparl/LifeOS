"""The owner's side of a shared trip plan: the link, its settings, versions, lock and apply.

Every method starts from the owner's trip, so another user's trip (or share) is a plain 404.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ServiceUnavailableError, get_or_404
from app.core.short_codes import generate_code
from app.core.timezone import utc_now
from app.modules.auth.models import User
from app.modules.travel.models import (
    TravelShareContributor,
    TravelShareEvent,
    TravelShareVersion,
    TravelTrip,
    TravelTripShare,
)
from app.modules.travel.plan_document import summarize
from app.modules.travel.repository.shares import ShareRepository
from app.modules.travel.repository.trips import TripRepository
from app.modules.travel.schemas.plan_document import PlanDocument
from app.modules.travel.schemas.shares import (
    ApplyResult,
    ContributorOut,
    EventOut,
    LockResult,
    ShareOut,
    ShareSettingsUpdate,
    VersionDetail,
    VersionRow,
)
from app.modules.travel.services.export_service import ExportService
from app.modules.travel.services.share_apply import ShareApplyService

SHARE_CODE_LENGTH = 8  # 33^8 ≈ 1.4e12 codes
MAX_OWNER_VERSIONS = 5
ORIGINAL_LABEL = "Original"
TRIP_NOT_FOUND = "Trip not found"
SHARE_NOT_FOUND = "This trip has no share link"
VERSION_NOT_FOUND = "Version not found"


def share_url_path(code: str) -> str:
    return f"/t/{code}"


def owner_first_name(user: User) -> str:
    """The only owner detail friends ever see ("Send to <name>")."""
    first = (user.display_name or "").strip().split(" ")[0]
    return first or user.username


class ShareService:
    def __init__(self, db: AsyncSession):
        self.repo = ShareRepository(db)
        self.trip_repo = TripRepository(db)
        self.applier = ShareApplyService(db)
        self.export = ExportService(db)

    # ---- lookups ----------------------------------------------------------------------------

    async def _trip(self, user: User, trip_id: str) -> TravelTrip:
        return get_or_404(await self.trip_repo.get(user.id, trip_id), TRIP_NOT_FOUND)

    async def _share(self, user: User, trip_id: str) -> TravelTripShare:
        await self._trip(user, trip_id)
        return get_or_404(await self.repo.get_for_trip(user.id, trip_id), SHARE_NOT_FOUND)

    async def _version(self, share: TravelTripShare, version_id: str) -> TravelShareVersion:
        return get_or_404(await self.repo.get_version(share.id, version_id), VERSION_NOT_FOUND)

    async def _unique_code(self) -> str:
        for _ in range(5):
            code = generate_code(SHARE_CODE_LENGTH)
            if not await self.repo.code_exists(code):
                return code
        raise ServiceUnavailableError("Could not create a link. Please try again.")

    async def _event(self, share: TravelTripShare, user: User, action: str, version_id: str | None = None) -> None:
        await self.repo.add(
            TravelShareEvent(share_id=share.id, actor="owner", actor_id=user.id, action=action, version_id=version_id)
        )

    async def _new_version(
        self, share: TravelTripShare, kind: str, label: str, doc: PlanDocument
    ) -> TravelShareVersion:
        now = utc_now()
        version = TravelShareVersion(
            share_id=share.id, kind=kind, label=label, document=doc.model_dump(mode="json"), created_at=now,
            updated_at=now,
        )
        await self.repo.add(version)
        return version

    # ---- output -----------------------------------------------------------------------------

    async def _share_out(self, share: TravelTripShare) -> ShareOut:
        contributors = await self.repo.contributors(share.id)
        return ShareOut(
            id=share.id,
            trip_id=share.trip_id,
            code=share.code,
            url_path=share_url_path(share.code),
            state=share.state,
            require_google=share.require_google,
            allowed_emails=list(share.allowed_emails or []),
            original_version_id=share.original_version_id,
            locked_version_id=share.locked_version_id,
            created_at=share.created_at,
            locked_at=share.locked_at,
            revoked_at=share.revoked_at,
            contributors=[_contributor_out(c) for c in contributors],
        )

    async def _rows(self, user: User, share: TravelTripShare) -> list[VersionDetail]:
        versions = await self.repo.versions(share.id)
        contributors = {c.id: c for c in await self.repo.contributors(share.id)}
        original = next((v for v in versions if v.id == share.original_version_id), None)
        original_doc = PlanDocument.model_validate(original.document) if original else PlanDocument()
        return [_detail(v, share, original_doc, contributors, owner_first_name(user)) for v in versions]

    # ---- link -------------------------------------------------------------------------------

    async def create(self, user: User, trip_id: str) -> ShareOut:
        trip = await self._trip(user, trip_id)
        if await self.repo.get_for_trip(user.id, trip.id) is not None:
            raise ConflictError("This trip already has a share link")
        share = TravelTripShare(user_id=user.id, trip_id=trip.id, code=await self._unique_code(), state="open")
        await self.repo.add(share)
        original = await self._new_version(
            share, "original", ORIGINAL_LABEL, await self.applier.trip_document(user.id, trip.id)
        )
        share.original_version_id = original.id
        await self._event(share, user, "create", original.id)
        return await self._share_out(share)

    async def get(self, user: User, trip_id: str) -> ShareOut:
        return await self._share_out(await self._share(user, trip_id))

    async def update_settings(self, user: User, trip_id: str, data: ShareSettingsUpdate) -> ShareOut:
        share = await self._share(user, trip_id)
        if data.require_google is not None:
            share.require_google = data.require_google
        if data.allowed_emails is not None:
            share.allowed_emails = data.allowed_emails
        await self._event(share, user, "settings")
        return await self._share_out(share)

    async def revoke(self, user: User, trip_id: str) -> ShareOut:
        share = await self._share(user, trip_id)
        share.state = "revoked"
        share.revoked_at = utc_now()
        await self._event(share, user, "revoke")
        return await self._share_out(share)

    async def new_link(self, user: User, trip_id: str) -> ShareOut:
        """A fresh code for the same share; the old one stops working. Plans and friends are kept."""
        share = await self._share(user, trip_id)
        share.code = await self._unique_code()
        if share.state == "revoked":
            share.state = "locked" if share.locked_version_id else "open"
            share.revoked_at = None
        await self._event(share, user, "new_link")
        return await self._share_out(share)

    # ---- lock -------------------------------------------------------------------------------

    async def lock(self, user: User, trip_id: str, version_id: str, apply: bool) -> LockResult:
        trip = await self._trip(user, trip_id)
        share = await self._share(user, trip_id)
        if share.state == "revoked":
            raise ConflictError("This link is turned off. Create a new link first.")
        version = await self._version(share, version_id)
        if version.kind == "backup":
            raise ConflictError("A backup can't be the final plan. Apply it to your trip instead.")
        applied = await self.applier.apply(trip, share, version) if apply else None
        share.state = "locked"
        share.locked_version_id = version.id
        share.locked_at = utc_now()
        await self._event(share, user, "lock", version.id)
        if applied is not None:
            await self._event(share, user, "apply", version.id)
        return LockResult(share=await self._share_out(share), applied=applied)

    async def unlock(self, user: User, trip_id: str) -> ShareOut:
        share = await self._share(user, trip_id)
        if share.state != "locked":
            raise ConflictError("This plan is not locked")
        share.state = "open"
        share.locked_version_id = None
        share.locked_at = None
        await self._event(share, user, "unlock")
        return await self._share_out(share)

    # ---- versions ---------------------------------------------------------------------------

    async def list_versions(self, user: User, trip_id: str) -> list[VersionRow]:
        share = await self._share(user, trip_id)
        return [VersionRow.model_validate(row.model_dump(exclude={"document"})) for row in await self._rows(user, share)]

    async def get_version(self, user: User, trip_id: str, version_id: str) -> VersionDetail:
        share = await self._share(user, trip_id)
        await self._version(share, version_id)
        return next(row for row in await self._rows(user, share) if row.id == version_id)

    async def rename_version(self, user: User, trip_id: str, version_id: str, label: str) -> VersionRow:
        share = await self._share(user, trip_id)
        version = await self._version(share, version_id)
        version.label = label
        await self.repo.flush()
        return await self._row(user, share, version_id)

    async def delete_version(self, user: User, trip_id: str, version_id: str) -> None:
        share = await self._share(user, trip_id)
        version = await self._version(share, version_id)
        if version.id == share.original_version_id:
            raise ConflictError("The Original can't be deleted")
        if version.id == share.locked_version_id:
            raise ConflictError("Unlock first: this is the final plan")
        await self._event(share, user, "delete_version", version.id)
        await self.repo.delete_version(version)

    async def snapshot_trip(self, user: User, trip_id: str) -> VersionRow:
        """"Save my current trip as a version", to compare with friends' plans (requirements T-22)."""
        share = await self._share(user, trip_id)
        owned = await self.repo.versions_of_kind(share.id, "owner")
        if len(owned) >= MAX_OWNER_VERSIONS:
            raise ConflictError(f"You can keep up to {MAX_OWNER_VERSIONS} of your own versions. Delete one first.")
        label = f"{owner_first_name(user)}'s plan" + (f" {len(owned) + 1}" if owned else "")
        version = await self._new_version(share, "owner", label, await self.applier.trip_document(user.id, trip_id))
        return await self._row(user, share, version.id)

    async def apply(self, user: User, trip_id: str, version_id: str) -> ApplyResult:
        trip = await self._trip(user, trip_id)
        share = await self._share(user, trip_id)
        version = await self._version(share, version_id)
        result = await self.applier.apply(trip, share, version)
        await self._event(share, user, "apply", version.id)
        return result

    async def version_pdf(self, user: User, trip_id: str, version_id: str) -> tuple[bytes, str]:
        share = await self._share(user, trip_id)
        version = await self._version(share, version_id)
        return await self.export.plan_pdf(user.id, trip_id, PlanDocument.model_validate(version.document), version.label)

    async def _row(self, user: User, share: TravelTripShare, version_id: str) -> VersionRow:
        row = next(row for row in await self._rows(user, share) if row.id == version_id)
        return VersionRow.model_validate(row.model_dump(exclude={"document"}))

    # ---- contributors and events ------------------------------------------------------------

    async def remove_contributor(self, user: User, trip_id: str, contributor_id: str) -> ShareOut:
        share = await self._share(user, trip_id)
        contributor = get_or_404(await self.repo.get_contributor(share.id, contributor_id), "Person not found")
        if contributor.removed_at is None:
            contributor.removed_at = utc_now()
            contributor.secret_hash = None  # this device can no longer renew its access
            await self._event(share, user, "remove_contributor")
        return await self._share_out(share)

    async def events(self, user: User, trip_id: str, limit: int) -> list[EventOut]:
        share = await self._share(user, trip_id)
        return [
            EventOut(action=e.action, actor=e.actor, version_id=e.version_id, at=e.at)
            for e in await self.repo.events(share.id, limit)
        ]


def _contributor_out(c: TravelShareContributor) -> ContributorOut:
    return ContributorOut(
        id=c.id,
        kind=c.kind,
        display_name=c.display_name,
        google_email=c.google_email,
        removed=c.removed_at is not None,
        created_at=c.created_at,
        last_seen_at=c.last_seen_at,
    )


def _detail(
    version: TravelShareVersion,
    share: TravelTripShare,
    original: PlanDocument,
    contributors: dict[str, TravelShareContributor],
    owner_name: str,
) -> VersionDetail:
    doc = PlanDocument.model_validate(version.document)
    contributor = contributors.get(version.contributor_id) if version.contributor_id else None
    if contributor is not None:
        author_kind, author_name, author_email = "contributor", contributor.display_name, contributor.google_email
    elif version.kind in ("original", "backup"):
        author_kind, author_name, author_email = "system", owner_name, None
    else:
        author_kind, author_name, author_email = "owner", owner_name, None
    return VersionDetail(
        id=version.id,
        kind=version.kind,
        label=version.label,
        status=version.status,
        author_kind=author_kind,
        author_name=author_name,
        author_email=author_email,
        contributor_removed=contributor is not None and contributor.removed_at is not None,
        is_locked=version.id == share.locked_version_id,
        edited_since_sent=version.submitted_revision is not None and version.revision != version.submitted_revision,
        message=version.message,
        revision=version.revision,
        created_at=version.created_at,
        updated_at=version.updated_at,
        submitted_at=version.submitted_at,
        summary=summarize(original, doc),
        document=doc,
    )
