"""Travel OS tables. Every root row carries `user_id`; child rows are reached through their owner.

Coordinates are plain floats with a composite `(user_id, lat, lng)` index: "near" queries use a
bounding-box prefilter plus an exact haversine check (see `geo.py`), which works on SQLite and
Postgres without PostGIS.
"""

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, new_id
from app.core.timezone import utc_now

PLACE_STATUSES = ("wishlist", "planned", "visited", "favourite")
PLACE_CATEGORIES = (
    "trek",
    "mountain",
    "city",
    "beach",
    "nature",
    "photography",
    "camping",
    "road_trip",
    "adventure",
    "other",
)
TRIP_STATUSES = ("draft", "planning", "booked", "active", "completed")
ROUTE_SOURCES = ("google", "user_drawn", "gpx", "straight_line")
ROUTE_MODES = ("driving", "walking", "cycling", "transit")
ADVENTURE_KINDS = ("trek", "hike", "road_trip", "camping", "cycling", "expedition")
ADVENTURE_DIFFICULTIES = ("easy", "moderate", "hard", "expert")
WAYPOINT_KINDS = ("start", "camp", "summit", "water", "viewpoint", "end", "other")
USAGE_OUTCOMES = ("ok", "error", "blocked")


def _created() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), default=utc_now)


def _updated() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


def _owner() -> Mapped[str]:
    return mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)


class TravelPlace(Base):
    __tablename__ = "travel_places"
    __table_args__ = (
        Index("ix_travel_places_user_coords", "user_id", "lat", "lng"),
        Index("ix_travel_places_user_status", "user_id", "status"),
        UniqueConstraint("user_id", "external_place_id", name="uq_travel_places_user_external"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = _owner()
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    country: Mapped[str | None] = mapped_column(String(80), nullable=True)
    region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    external_place_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_source: Mapped[str | None] = mapped_column(String(16), nullable=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="other")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="wishlist")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    desired_period: Mapped[str | None] = mapped_column(String(80), nullable=True)
    estimated_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    links: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class TravelTag(Base):
    __tablename__ = "travel_tags"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_travel_tags_user_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = _owner()
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = _created()


class TravelPlaceTag(Base):
    __tablename__ = "travel_place_tags"

    place_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("travel_places.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("travel_tags.id", ondelete="CASCADE"), primary_key=True, index=True
    )


class TravelTrip(Base):
    __tablename__ = "travel_trips"
    __table_args__ = (
        Index("ix_travel_trips_user_status", "user_id", "status"),
        Index("ix_travel_trips_user_start", "user_id", "start_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = _owner()
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    dates_tentative: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    cover_photo_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class TravelTripPlace(Base):
    __tablename__ = "travel_trip_places"
    __table_args__ = (UniqueConstraint("trip_id", "place_id", name="uq_travel_trip_places"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("travel_trips.id", ondelete="CASCADE"), index=True, nullable=False
    )
    place_id: Mapped[str] = mapped_column(String(36), ForeignKey("travel_places.id"), index=True, nullable=False)
    # True when confirming this trip moved the place from wishlist -> planned (undone on revert).
    promoted_place: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = _created()


class TravelItineraryDay(Base):
    __tablename__ = "travel_itinerary_days"
    __table_args__ = (UniqueConstraint("trip_id", "day_index", name="uq_travel_days_trip_index"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("travel_trips.id", ondelete="CASCADE"), index=True, nullable=False
    )
    day_index: Mapped[int] = mapped_column(Integer, nullable=False)
    day_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = _created()


class TravelItineraryItem(Base):
    __tablename__ = "travel_itinerary_items"
    __table_args__ = (Index("ix_travel_items_day_position", "day_id", "position"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("travel_trips.id", ondelete="CASCADE"), index=True, nullable=False
    )
    day_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("travel_itinerary_days.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    place_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("travel_places.id"), index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    transport: Mapped[str | None] = mapped_column(String(120), nullable=True)
    accommodation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    links: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class TravelRoute(Base):
    __tablename__ = "travel_routes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = _owner()
    trip_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("travel_trips.id", ondelete="CASCADE"), index=True, nullable=True
    )
    adventure_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False, default="driving")
    distance_m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    duration_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    polyline: Mapped[str] = mapped_column(Text, nullable=False, default="")
    elevation_gain_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    elevation_loss_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Encoded elevation profile (GPX samples or Google lookup); JSON list of metres, capped.
    elevation_profile: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # Google road legs, one per consecutive stop pair: [{distance_m, duration_s, polyline}]. Null for fallbacks.
    legs: Mapped[list | None] = mapped_column(JSON, nullable=True)
    stops_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fallback_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    gpx_file_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class TravelRouteWaypoint(Base):
    __tablename__ = "travel_route_waypoints"
    __table_args__ = (Index("ix_travel_route_waypoints_route_position", "route_id", "position"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    route_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("travel_routes.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    place_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class TravelAdventure(Base):
    __tablename__ = "travel_adventures"
    __table_args__ = (Index("ix_travel_adventures_user_trip", "user_id", "trip_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = _owner()
    trip_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("travel_trips.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default="trek")
    difficulty: Mapped[str | None] = mapped_column(String(16), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    route_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class TravelAdventureWaypoint(Base):
    __tablename__ = "travel_adventure_waypoints"
    __table_args__ = (Index("ix_travel_adv_waypoints_adv_position", "adventure_id", "position"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    adventure_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("travel_adventures.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default="other")
    elevation_m: Mapped[float | None] = mapped_column(Float, nullable=True)


class TravelPhoto(Base):
    __tablename__ = "travel_photos"
    __table_args__ = (Index("ix_travel_photos_user_coords", "user_id", "lat", "lng"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = _owner()
    file_id: Mapped[str] = mapped_column(String(36), nullable=False)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_source: Mapped[str | None] = mapped_column(String(8), nullable=True)
    taken_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    caption: Mapped[str | None] = mapped_column(String(500), nullable=True)
    place_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    trip_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    day_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    adventure_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    journal_entry_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = _created()


class TravelJournalEntry(Base):
    __tablename__ = "travel_journal_entries"
    __table_args__ = (Index("ix_travel_journal_user_date", "user_id", "entry_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = _owner()
    trip_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    place_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    adventure_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    route_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class MapsUsageEvent(Base):
    __tablename__ = "maps_usage_events"
    __table_args__ = (Index("ix_maps_usage_user_created", "user_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = _created()
    api: Mapped[str] = mapped_column(String(32), nullable=False)
    sku: Mapped[str] = mapped_column(String(32), nullable=False)
    feature: Mapped[str] = mapped_column(String(32), nullable=False)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    estimated_cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False, default=0)
    outcome: Mapped[str] = mapped_column(String(8), nullable=False)


class MapPricingConfiguration(Base):
    """Per-user editable rates (spec §31a). Seeded from `maps/pricing_defaults.py`; never read from code."""

    __tablename__ = "map_pricing_configurations"
    __table_args__ = (UniqueConstraint("user_id", "sku", name="uq_map_pricing_user_sku"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = _owner()
    sku: Mapped[str] = mapped_column(String(32), nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    unit_price_usd_per_1000: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    free_monthly_units: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = _updated()


class TravelMapsSettings(Base):
    __tablename__ = "travel_maps_settings"
    __table_args__ = (UniqueConstraint("user_id", name="uq_travel_maps_settings_user"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    protection_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    budget_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=500)
    warning_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=350)
    budget_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    stop_at_free_tier: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fx_rates: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pricing_last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = _updated()


# ---- shared trip plans (public /t/<code> planner) --------------------------------------------------

SHARE_STATES = ("open", "locked", "revoked")
CONTRIBUTOR_KINDS = ("google", "name")
VERSION_KINDS = ("original", "plan", "owner", "backup")
VERSION_STATUSES = ("draft", "submitted")


class TravelTripShare(Base):
    """At most one per trip. Friends reach it by `code`; the owner manages it from the trip."""

    __tablename__ = "travel_trip_shares"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = _owner()
    trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("travel_trips.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    code: Mapped[str] = mapped_column(String(8), unique=True, index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(8), nullable=False, default="open")
    require_google: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allowed_emails: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    original_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    locked_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TravelShareContributor(Base):
    """A friend on one share (never a LifeOS user): a Google account or a name plus a device secret."""

    __tablename__ = "travel_share_contributors"
    __table_args__ = (UniqueConstraint("share_id", "google_sub", name="uq_travel_share_contributor_sub"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    share_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("travel_trip_shares.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[str] = mapped_column(String(8), nullable=False)
    display_name: Mapped[str] = mapped_column(String(40), nullable=False)
    google_sub: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # SHA-256 of the one active device secret; the secret itself only lives in the friend's browser.
    secret_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = _created()
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TravelShareVersion(Base):
    """A snapshot document of an itinerary. Never touches the trip tables until the owner applies it.

    `updated_at` moves only when the document changes (no `onupdate`), so the owner's list is
    "latest edited first", not "latest renamed first".
    """

    __tablename__ = "travel_share_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    share_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("travel_trip_shares.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(8), nullable=False)
    contributor_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="draft")
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    document: Mapped[dict] = mapped_column(JSON, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    submitted_revision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


Index(
    "ix_travel_share_versions_share_updated",
    TravelShareVersion.share_id,
    TravelShareVersion.updated_at.desc(),
)


class TravelShareEvent(Base):
    """Append-only audit trail of owner and contributor actions on a share (lock, unlock, apply, ...)."""

    __tablename__ = "travel_share_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    share_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("travel_trip_shares.id", ondelete="CASCADE"), index=True, nullable=False
    )
    actor: Mapped[str] = mapped_column(String(16), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(24), nullable=False)
    version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    at: Mapped[datetime] = _created()
