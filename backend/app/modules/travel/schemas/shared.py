"""Public shapes for the friend planner at /t/<code>.

Each model lists exactly the fields it may return (requirements NFR-SEC): no owner id or email, no
trip notes, photos, journal, budgets or other places, no other contributors, no secret hashes.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.modules.travel.schemas.common import Lat, Lng, OptText500, Text40
from app.modules.travel.schemas.plan_document import MAX_ROUTE_POINTS, PlanDocument, RoadLeg


class PublicTrip(BaseModel):
    name: str
    description: str | None
    start_date: date | None
    end_date: date | None


class PlanLimits(BaseModel):
    max_days: int
    max_stops: int


class PublicPlanView(BaseModel):
    trip: PublicTrip
    owner_name: str
    state: Literal["open", "locked"]
    # "Just use my name" is offered only when the owner allows it (no Google requirement, no allow-list).
    names_allowed: bool
    google_enabled: bool
    is_final: bool
    viewer_is_owner: bool
    # Only for the signed-in owner: where to manage this plan in LifeOS.
    manage_path: str | None = None
    plan: PlanDocument
    limits: PlanLimits


class JoinName(BaseModel):
    name: Text40


class GoogleCredential(BaseModel):
    credential: Annotated[str, Field(min_length=10, max_length=4096)]


class SessionRenew(BaseModel):
    device_secret: Annotated[str, Field(min_length=16, max_length=64)]


class ContributorMe(BaseModel):
    id: str
    kind: Literal["google", "name"]
    display_name: str


class MyPlanOut(BaseModel):
    id: str
    status: Literal["draft", "submitted"]
    revision: int
    updated_at: datetime
    submitted_at: datetime | None
    edited_since_sent: bool
    document: PlanDocument


class MyView(BaseModel):
    contributor: ContributorMe
    plan: MyPlanOut | None


class SessionOut(MyView):
    token: str
    expires_at: datetime


class JoinOut(SessionOut):
    """Returned once: the device secret is shown here and never again (only its hash is stored)."""

    device_secret: str


class OwnerHint(BaseModel):
    """A Google sign-in that turned out to be the trip owner: nothing is created."""

    owner: Literal[True] = True


class SubmitIn(BaseModel):
    message: OptText500 = None


class ResolvedLink(BaseModel):
    name: str | None = None
    lat: float | None = None
    lng: float | None = None
    google_place_id: str | None = None


class RoadRouteIn(BaseModel):
    """One day's leg chain (see `plan_document.day_chains`), routed by road."""

    points: list[tuple[Lat, Lng]] = Field(min_length=2, max_length=MAX_ROUTE_POINTS)


class RoadRouteOut(BaseModel):
    """`legs` is empty when no road route could be had; `fallback_reason` says why."""

    mode: Literal["driving"] = "driving"
    legs: list[RoadLeg]
    fallback_reason: str | None = None
