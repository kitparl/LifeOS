"""Property-based tests for synced-run matching and its reversible operations (Unit 1: running-sync).

Partial PBT enforcement: invariants (PBT-03) for the pure match rule and round-trips (PBT-02) for
attach/detach and sync/revert. Complements the example tests in test_running_sync.py.

Plain (non-async) tests: DB-backed properties open a short-lived asyncio.run() per example, as in
test_communication_vocabulary_pbt.py.
"""

import asyncio
from datetime import date, datetime, timedelta, timezone

import app.modules.calendar.models  # noqa: F401  (registers tables used by race calendar mirroring)
from app.core.database import Base
from app.modules.auth.models import User
from app.modules.running.contracts import SyncedRunInput
from app.modules.running.matching import MATCH_DISTANCE_TOLERANCE, MatchCandidate, find_match
from app.modules.running.models import RaceEvent, Run
from app.modules.running.service import RunningService
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

RUN_DAY = date(2026, 5, 3)
RUN_START = datetime(2026, 5, 3, 6, 0, tzinfo=timezone.utc)

# --- Generators (PBT-07: shaped like real runs, not raw primitives) -------------------------------

run_km = st.floats(min_value=0.5, max_value=100.0, allow_nan=False, allow_infinity=False).map(lambda v: round(v, 2))
run_seconds = st.integers(min_value=120, max_value=36_000)
finish_seconds = st.one_of(st.none(), st.integers(min_value=600, max_value=36_000))


@st.composite
def candidate_lists(draw) -> list[MatchCandidate]:
    distances = draw(st.lists(run_km, max_size=6))
    base = datetime(2026, 5, 3, 8, 0, tzinfo=timezone.utc)
    return [MatchCandidate(f"run-{i}", km, base + timedelta(minutes=i)) for i, km in enumerate(distances)]


def _within(candidate: MatchCandidate, activity_km: float) -> bool:
    return abs(candidate.distance_km - activity_km) / activity_km <= MATCH_DISTANCE_TOLERANCE


# --- Pure match rule -----------------------------------------------------------------------------


@given(activity_km=run_km, candidates=candidate_lists())
@settings(max_examples=200)
def test_match_is_none_or_a_candidate_within_tolerance(activity_km, candidates):
    matched = find_match(activity_km, candidates)

    if matched is None:
        assert not any(_within(c, activity_km) for c in candidates)
    else:
        chosen = next(c for c in candidates if c.run_id == matched)
        assert _within(chosen, activity_km)


@given(activity_km=run_km, candidates=candidate_lists())
@settings(max_examples=200)
def test_match_is_the_closest_candidate(activity_km, candidates):
    matched = find_match(activity_km, candidates)

    if matched is not None:
        chosen = next(c for c in candidates if c.run_id == matched)
        closest = min(abs(c.distance_km - activity_km) for c in candidates if _within(c, activity_km))
        assert abs(chosen.distance_km - activity_km) == closest


# --- Round-trips against a real (in-memory) database ---------------------------------------------


async def _with_db(work):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as db:
            user = User(email="pbt@example.com", username="pbtuser", hashed_password="x", display_name="P")
            db.add(user)
            await db.flush()
            return await work(db, user.id)
    finally:
        await engine.dispose()


def _activity(km: float, seconds: int) -> SyncedRunInput:
    return SyncedRunInput("act-1", "garmin", RUN_START, None, km * 1000, float(seconds), float(seconds + 45))


@given(typed_km=run_km, typed_seconds=run_seconds, synced_seconds=run_seconds, drift=st.floats(-0.03, 0.03))
@settings(max_examples=25, deadline=None)
def test_sync_then_revert_restores_what_the_user_typed(typed_km, typed_seconds, synced_seconds, drift):
    # Stay strictly inside the tolerance so rounding never pushes the pair out of a match.
    synced_km = round(typed_km * (1 + drift * 0.9), 3)

    async def work(db, user_id):
        run = Run(user_id=user_id, run_date=RUN_DAY, distance_km=typed_km, duration_seconds=typed_seconds, notes="n")
        db.add(run)
        await db.flush()
        service = RunningService(db)
        synced = await service.sync_run_from_activity(user_id, _activity(synced_km, synced_seconds))
        await service.revert_runs_for_activities(user_id, ["act-1"])
        await db.refresh(run)
        return synced, run

    synced, run = asyncio.run(_with_db(work))

    assert synced.run_id == run.id and synced.matched_manual
    assert (run.distance_km, run.duration_seconds, run.notes) == (typed_km, typed_seconds, "n")
    assert (run.activity_id, run.manual_distance_km, run.manual_duration_seconds) == (None, None, None)


@given(finish=finish_seconds, attended=st.booleans(), synced_seconds=run_seconds)
@settings(max_examples=25, deadline=None)
def test_attach_then_detach_restores_the_race(finish, attended, synced_seconds):
    async def work(db, user_id):
        race = RaceEvent(
            user_id=user_id, name="Race", race_date=RUN_DAY, distance_type="10k",
            finish_time_seconds=finish, attended=attended, bib_number="B7",
        )
        db.add(race)
        await db.flush()
        service = RunningService(db)
        run_id = (await service.sync_run_from_activity(user_id, _activity(10.0, synced_seconds))).run_id
        attached = await service.attach_run_to_race(user_id, race.id, run_id)
        detached = await service.detach_run_from_race(user_id, race.id)
        return attached, detached

    attached, detached = asyncio.run(_with_db(work))

    assert attached.finish_time_seconds == synced_seconds + 45 and attached.attended
    assert (detached.finish_time_seconds, detached.attended, detached.run_id) == (finish, attended, None)
    assert detached.bib_number == "B7"
