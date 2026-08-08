from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth.models import User
from app.modules.learning.schemas import (
    ConceptListItem,
    ConceptNoteCreate,
    ConceptNoteResponse,
    ConceptResponse,
    ConceptUpdate,
    LearningCreate,
    LearningListItem,
    LearningResponse,
    LearningUpdate,
    ResourceCreate,
    ResourceResponse,
    ResourceUpdate,
    SessionCreate,
    SessionResponse,
    SessionStats,
    TrackCreate,
    TrackDetail,
    TrackListItem,
    TrackProgress,
    TrackSeedRequest,
)
from app.modules.learning.seeder import SeedValidationError, seed_track
from app.modules.learning.service import LearningService

router = APIRouter(prefix="/learning", tags=["learning"])


# --- Legacy items ---


@router.get("/items", response_model=list[LearningListItem])
async def list_learning(
    item_type: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).list_items(user.id, item_type)


@router.post("/items", response_model=LearningResponse, status_code=status.HTTP_201_CREATED)
async def create_learning(
    data: LearningCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).create_item(user.id, data)


@router.get("/items/{item_id}", response_model=LearningResponse)
async def get_learning(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).get_item(user.id, item_id)


@router.patch("/items/{item_id}", response_model=LearningResponse)
async def update_learning(
    item_id: str,
    data: LearningUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).update_item(user.id, item_id, data)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_learning(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await LearningService(db).delete_item(user.id, item_id)


# --- Tracks ---


@router.get("/tracks", response_model=list[TrackListItem])
async def list_tracks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).list_tracks(user.id)


@router.post("/tracks", response_model=TrackListItem, status_code=status.HTTP_201_CREATED)
async def create_track(
    data: TrackCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).create_track(user.id, data)


@router.post("/tracks/seed", response_model=TrackDetail, status_code=status.HTTP_201_CREATED)
async def seed_learning_track(
    data: TrackSeedRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException

    try:
        track = await seed_track(db, user.id, data.slug)
    except SeedValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return await LearningService(db).get_track(user.id, track.id)


@router.get("/tracks/{track_id}", response_model=TrackDetail)
async def get_track(
    track_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).get_track(user.id, track_id)


@router.get("/tracks/{track_id}/progress", response_model=TrackProgress)
async def get_track_progress(
    track_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).track_progress(user.id, track_id)


# --- Concepts ---


@router.get("/concepts", response_model=list[ConceptListItem])
async def list_concepts(
    item_id: str | None = Query(default=None),
    week: int | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).list_concepts(user.id, item_id, week)


@router.get("/concepts/{concept_id}", response_model=ConceptResponse)
async def get_concept(
    concept_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).get_concept(user.id, concept_id)


@router.patch("/concepts/{concept_id}", response_model=ConceptResponse)
async def update_concept(
    concept_id: str,
    data: ConceptUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).update_concept(user.id, concept_id, data)


# --- Concept notes ---


@router.get("/concepts/{concept_id}/notes", response_model=list[ConceptNoteResponse])
async def list_concept_notes(
    concept_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).list_concept_notes(user.id, concept_id)


@router.post(
    "/concepts/{concept_id}/notes",
    response_model=ConceptNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def attach_concept_note(
    concept_id: str,
    data: ConceptNoteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).attach_concept_note(user.id, concept_id, data)


@router.delete(
    "/concepts/{concept_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def detach_concept_note(
    concept_id: str,
    note_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await LearningService(db).detach_concept_note(user.id, concept_id, note_id)


# --- Resources ---


@router.get("/resources", response_model=list[ResourceResponse])
async def list_resources(
    concept_id: str | None = Query(default=None),
    item_id: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).list_resources(user.id, concept_id, item_id)


@router.post("/resources", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    data: ResourceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).create_resource(user.id, data)


@router.patch("/resources/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: str,
    data: ResourceUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).update_resource(user.id, resource_id, data)


# --- Sessions ---


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).list_sessions(user.id, from_date, to_date)


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).create_session(user.id, data)


@router.get("/sessions/stats", response_model=SessionStats)
async def session_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await LearningService(db).session_stats(user.id)
