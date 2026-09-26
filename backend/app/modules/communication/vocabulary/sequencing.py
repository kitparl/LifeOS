"""The single authoritative sequence-allocation and daily-state-machine logic.

PRD §62 rule 1 ("business-critical vocabulary sequencing logic must have one
authoritative implementation") — every code path that consumes NEW vocabulary
(daily rollover, Change, Next Set) calls ``allocate_next`` here and nowhere else.
Revision, games, and bookmarks never call it (PRD §62 rules 11-13).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.core.timezone import ist_today, utc_now
from app.modules.auth.models import User
from app.modules.communication.vocabulary.models import Vocabulary, VocabularySet
from app.modules.communication.vocabulary.repository import VocabularyRepository

DAILY_SET_SIZE = 10



async def allocate_next(db: AsyncSession, repo: VocabularyRepository, user: User, count: int) -> list[Vocabulary]:
    """Lock the user's progress row, take the next `count` unused vocabulary items,
    record them as consumed, advance the pointer. Transaction-safe (PRD §19-20)."""
    progress = await repo.get_progress_locked(user.id)
    if progress is None:
        progress = repo.new_progress(user.id)
        try:
            await db.flush()
        except IntegrityError as exc:
            # Extremely-rare first-request race: another concurrent request for the same
            # brand-new user already created the progress row. Ask the caller to retry —
            # on retry, the locked SELECT above will find and lock the now-existing row.
            raise ConflictError("Vocabulary progress initialization conflict — please retry") from exc

    start = progress.next_sequence_number
    rows = await repo.get_next_unused(start, count)
    now = utc_now()
    for v in rows:
        repo.new_user_vocabulary(user.id, v.id, now)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise ConflictError("Vocabulary allocation conflict — please retry") from exc

    progress.next_sequence_number = start + len(rows)
    await db.flush()
    return rows


async def create_set(
    db: AsyncSession, repo: VocabularyRepository, user: User, set_type: str
) -> VocabularySet | None:
    """Allocate DAILY_SET_SIZE new items and materialize them as a set. Returns None
    (creates nothing) when the master dataset has no unused items left (PRD §53)."""
    vocab_rows = await allocate_next(db, repo, user, DAILY_SET_SIZE)
    if not vocab_rows:
        return None
    vset = repo.new_set(user.id, set_type, ist_today(), status="active")
    await db.flush()
    for position, v in enumerate(vocab_rows, start=1):
        repo.new_set_item(vset.id, user.id, v.id, v.sequence_number, position)
    progress = await repo.get_progress(user.id)
    if progress is not None:
        progress.active_set_id = vset.id
    await db.flush()
    return vset


@dataclass
class DailyStateResult:
    state: str  # NO_ACTIVE_SET | ACTIVE | ACTIVE_NEXT_SET | WAITING_FOR_NEXT_MIDNIGHT
    current_set: VocabularySet | None
    end_of_dataset: bool


async def resolve_daily_state(db: AsyncSession, repo: VocabularyRepository, user: User) -> DailyStateResult:
    """Compute daily eligibility on every read — no cron dependency (PRD §32).

    Midnight alone never advances an unaccepted set (PRD §62 rule 9): an ACTIVE set is
    returned unchanged regardless of date until the user accepts it.
    """
    latest = await repo.get_latest_set(user.id)

    if latest is None:
        new_set = await create_set(db, repo, user, "daily")
        if new_set is None:
            return DailyStateResult(state="NO_ACTIVE_SET", current_set=None, end_of_dataset=True)
        return DailyStateResult(state="ACTIVE", current_set=new_set, end_of_dataset=False)

    if latest.status == "active":
        return DailyStateResult(state="ACTIVE", current_set=latest, end_of_dataset=False)

    # latest.status == "accepted"
    if ist_today() > latest.set_date:
        new_set = await create_set(db, repo, user, "daily")
        if new_set is None:
            return DailyStateResult(state="WAITING_FOR_NEXT_MIDNIGHT", current_set=latest, end_of_dataset=True)
        return DailyStateResult(state="ACTIVE_NEXT_SET", current_set=new_set, end_of_dataset=False)

    return DailyStateResult(state="WAITING_FOR_NEXT_MIDNIGHT", current_set=latest, end_of_dataset=False)
