"""Shared trip plans test support: domain generators (PBT-07) and owner-side setup helpers."""

from __future__ import annotations

import uuid

from app.modules.travel.models import TravelShareVersion
from app.modules.travel.schemas.plan_document import PlanDay, PlanDocument, PlanPlace, PlanStop
from app.modules.travel.schemas.trips import MAX_TRIP_DAYS
from app.tests.test_travel_trips import _dated_itinerary, _himachal
from hypothesis import strategies as st
from sqlalchemy import select

BASE = "/api/v1/travel"

# ---- generators --------------------------------------------------------------------------------

_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs", "Cc")), min_size=1, max_size=40
).filter(lambda s: s.strip())
_opt_text = st.none() | _text
_times = st.none() | st.times().map(lambda t: t.replace(second=0, microsecond=0))
_links = st.lists(
    st.from_regex(r"https://[a-z]{1,12}\.example\.com/[a-z0-9]{0,10}", fullmatch=True), max_size=3
)


def lat_lngs():
    return st.tuples(
        st.floats(min_value=-89.0, max_value=89.0, allow_nan=False),
        st.floats(min_value=-179.0, max_value=179.0, allow_nan=False),
    )


def plan_places():
    google_ids = st.none() | st.from_regex(r"ChIJ[A-Za-z0-9_-]{6,20}", fullmatch=True)
    return st.builds(
        lambda ll, name, gid: PlanPlace(name=name, lat=ll[0], lng=ll[1], google_place_id=gid),
        lat_lngs(),
        _text,
        google_ids,
    )


def plan_stops():
    return st.builds(
        PlanStop,
        id=st.uuids().map(str),
        title=_text,
        kind=st.sampled_from(["stay", "food", "travel", "sightseeing", "rest", "other"]),
        place=st.none() | plan_places(),
        start_time=_times,
        end_time=_times,
        transport=_opt_text,
        stay=_opt_text,
        notes=_opt_text,
        links=_links,
    )


def plan_documents(max_days: int = 6, max_stops: int = 6):
    """Valid documents, including the empty plan, empty days and stops without a place."""
    days = st.lists(
        st.builds(PlanDay, title=_opt_text, notes=_opt_text, stops=st.lists(plan_stops(), max_size=max_stops)),
        max_size=min(max_days, MAX_TRIP_DAYS),
    )
    return days.map(lambda ds: PlanDocument(days=_unique_ids(ds)))


def _unique_ids(days: list[PlanDay]) -> list[PlanDay]:
    """Generated uuids are unique in practice; enforce it so shrinking never yields a duplicate."""
    seen: set[str] = set()
    for day in days:
        for stop in day.stops:
            if stop.id in seen:
                stop.id = str(uuid.uuid4())
            seen.add(stop.id)
    return days


# ---- API setup ---------------------------------------------------------------------------------


async def shared_trip(client, h) -> tuple[str, dict, dict]:
    """A dated two-stop-day trip with a share link. Returns (trip_id, places, share)."""
    places, tid = await _himachal(client, h)
    await _dated_itinerary(client, h, places, tid)
    share = await client.post(f"{BASE}/trips/{tid}/share", headers=h)
    assert share.status_code == 201, share.text
    return tid, places, share.json()


async def add_friend_plan(client, share_id: str, doc: PlanDocument, label: str = "Asha's plan") -> str:
    """A friend's plan written straight to the table (the public API is exercised in its own tests)."""
    async with client.session_factory() as session:
        version = TravelShareVersion(
            share_id=share_id, kind="plan", label=label, status="submitted", document=doc.model_dump(mode="json")
        )
        session.add(version)
        await session.commit()
        return version.id


async def rows(client, model, **where):
    async with client.session_factory() as session:
        stmt = select(model).filter_by(**where) if where else select(model)
        return list((await session.execute(stmt)).scalars().all())
