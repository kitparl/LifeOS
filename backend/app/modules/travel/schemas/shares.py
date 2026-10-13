"""Owner-side shapes for a trip's share link and its plan versions (authenticated, owner only)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, EmailStr, Field

from app.modules.travel.schemas.common import EntityId, Text80
from app.modules.travel.schemas.plan_document import PlanDocument

ShareState = Literal["open", "locked", "revoked"]
VersionKind = Literal["original", "plan", "owner", "backup"]
VersionStatus = Literal["draft", "submitted"]
AuthorKind = Literal["owner", "contributor", "system"]
MAX_ALLOWED_EMAILS = 50


def _normalize_emails(values: list[str] | None) -> list[str] | None:
    if values is None:
        return None
    return sorted({v.strip().lower() for v in values})


class ContributorOut(BaseModel):
    id: str
    kind: Literal["google", "name"]
    display_name: str
    google_email: str | None
    removed: bool
    created_at: datetime
    last_seen_at: datetime | None


class ShareOut(BaseModel):
    id: str
    trip_id: str
    code: str
    url_path: str
    state: ShareState
    require_google: bool
    allowed_emails: list[str]
    original_version_id: str | None
    locked_version_id: str | None
    created_at: datetime
    locked_at: datetime | None
    revoked_at: datetime | None
    contributors: list[ContributorOut]


class ShareSettingsUpdate(BaseModel):
    require_google: bool | None = None
    allowed_emails: Annotated[
        list[EmailStr] | None, Field(default=None, max_length=MAX_ALLOWED_EMAILS), AfterValidator(_normalize_emails)
    ] = None


class PlanSummary(BaseModel):
    """A version compared with the Original, by stop id. Distances are straight-line estimates."""

    days: int
    stops: int
    added: int
    removed: int
    changed: int
    km: float


class VersionRow(BaseModel):
    id: str
    kind: VersionKind
    label: str
    status: VersionStatus
    author_kind: AuthorKind
    author_name: str
    author_email: str | None
    contributor_removed: bool
    is_locked: bool
    edited_since_sent: bool
    message: str | None
    revision: int
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None
    summary: PlanSummary


class VersionDetail(VersionRow):
    document: PlanDocument


class VersionRename(BaseModel):
    label: Text80


class LockRequest(BaseModel):
    version_id: EntityId
    apply: bool = True


class ApplyResult(BaseModel):
    days: int
    items: int
    places_created: int
    places_reused: int
    backup_version_id: str
    end_date: date | None
    end_date_changed: bool


class LockResult(BaseModel):
    share: ShareOut
    applied: ApplyResult | None


class EventOut(BaseModel):
    action: str
    actor: AuthorKind
    version_id: str | None
    at: datetime
