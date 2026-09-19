from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.pagination import Pagination, pagination_params
from app.modules.auth.models import User
from app.modules.communication.schemas import (
    SpeakingCreate,
    SpeakingResponse,
    SpeakingUpdate,
    WritingCategoryCreate,
    WritingCreate,
    WritingEvaluationResponse,
    WritingResponse,
    WritingRewriteResponse,
    WritingUpdate,
)
from app.modules.communication.service import CommunicationService
from app.modules.communication.vocabulary.schemas import (
    BookmarkPage,
    BookmarkResponse,
    DailySetResponse,
    ExampleCreate,
    ExampleResponse,
    ExampleUpdate,
    GameAnswerCreate,
    GameAnswerResponse,
    GameHistoryPage,
    GameSessionCreate,
    GameSessionResponse,
    GameVocabularyPage,
    HistoryPage,
    ProgressResponse,
    VocabularyDetailResponse,
    VocabularyPage,
    VocabularySetResponse,
)
from app.modules.communication.vocabulary.service import VocabularyService

router = APIRouter(prefix="/communication", tags=["communication"])


# --------------------------------------------------------------------------
# Vocabulary — daily learning (Stage 1)
# --------------------------------------------------------------------------

@router.get("/vocabulary/today", response_model=DailySetResponse)
async def get_vocabulary_today(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).get_daily_set(user)


@router.post("/vocabulary/sets/{set_id}/accept", response_model=VocabularySetResponse)
async def accept_vocabulary_set(
    set_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).accept_current_set(user, set_id)


@router.post("/vocabulary/sets/{set_id}/items/{position}/change", response_model=VocabularySetResponse)
async def change_vocabulary_item(
    set_id: str,
    position: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).change_vocabulary_item(user, set_id, position)


@router.post("/vocabulary/sets/next", response_model=VocabularySetResponse)
async def next_vocabulary_set(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).get_next_set(user)


# --------------------------------------------------------------------------
# Vocabulary — fixed-path collection routes. MUST be registered before the
# /vocabulary/{vocabulary_id} catch-all detail route below, or FastAPI would
# match e.g. "search" as an id.
# --------------------------------------------------------------------------

@router.get("/vocabulary/bookmarks", response_model=BookmarkPage)
async def get_vocabulary_bookmarks(
    pagination: Pagination = Depends(pagination_params),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).get_bookmarks(user, pagination)


@router.get("/vocabulary/history", response_model=HistoryPage)
async def get_vocabulary_history(
    pagination: Pagination = Depends(pagination_params),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).get_history(user, pagination)


@router.get("/vocabulary/progress", response_model=ProgressResponse)
async def get_vocabulary_progress(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).get_progress(user)


@router.get("/vocabulary/search", response_model=VocabularyPage)
async def search_vocabulary(
    q: str | None = Query(default=None, max_length=200),
    level: str | None = None,
    type: str | None = None,
    part_of_speech: str | None = None,
    topic: str | None = Query(default=None, max_length=100),
    intent: str | None = Query(default=None, max_length=100),
    pagination: Pagination = Depends(pagination_params),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).search_vocabulary(
        q=q, level=level, type_=type, part_of_speech=part_of_speech, topic=topic, intent=intent,
        pagination=pagination,
    )


@router.get("/vocabulary/revision", response_model=VocabularyPage)
async def get_vocabulary_revision(
    source: str = Query(default="all"),
    target_date: date | None = Query(default=None, alias="date"),
    level: str | None = None,
    topic: str | None = None,
    pagination: Pagination = Depends(pagination_params),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).get_revision_vocabulary(
        user, source=source, target_date=target_date, level=level, topic=topic, pagination=pagination,
    )


# --------------------------------------------------------------------------
# Vocabulary — personal examples (fixed prefix, also before the catch-all)
# --------------------------------------------------------------------------

@router.patch("/vocabulary/examples/{example_id}", response_model=ExampleResponse)
async def update_vocabulary_example(
    example_id: str,
    payload: ExampleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).update_personal_example(user, example_id, payload)


@router.delete("/vocabulary/examples/{example_id}", status_code=204)
async def delete_vocabulary_example(
    example_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await VocabularyService(db).delete_personal_example(user, example_id)


# --------------------------------------------------------------------------
# Vocabulary — per-item routes
# --------------------------------------------------------------------------

@router.post("/vocabulary/bookmarks/{vocabulary_id}", response_model=BookmarkResponse)
async def add_vocabulary_bookmark(
    vocabulary_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).bookmark_vocabulary(user, vocabulary_id)


@router.delete("/vocabulary/bookmarks/{vocabulary_id}", status_code=204)
async def remove_vocabulary_bookmark(
    vocabulary_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await VocabularyService(db).remove_bookmark(user, vocabulary_id)


@router.get("/vocabulary/{vocabulary_id}/examples", response_model=list[ExampleResponse])
async def list_vocabulary_examples(
    vocabulary_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).list_personal_examples(user, vocabulary_id)


@router.post("/vocabulary/{vocabulary_id}/examples", response_model=ExampleResponse)
async def add_vocabulary_example(
    vocabulary_id: str,
    payload: ExampleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).add_personal_example(user, vocabulary_id, payload)


# --------------------------------------------------------------------------
# Vocabulary — games (Stage 3). All under /vocabulary/games/*, no collision
# with /vocabulary/{vocabulary_id}.
# --------------------------------------------------------------------------

@router.get("/vocabulary/games/vocabulary", response_model=GameVocabularyPage)
async def get_game_vocabulary(
    source: str = Query(...),
    level: str | None = None,
    target_date: date | None = Query(default=None, alias="date"),
    pagination: Pagination = Depends(pagination_params),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).get_game_vocabulary(
        user, source=source, level=level, target_date=target_date, pagination=pagination,
    )


@router.get("/vocabulary/games/history", response_model=GameHistoryPage)
async def get_game_history(
    pagination: Pagination = Depends(pagination_params),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).get_game_history(user, pagination)


@router.post("/vocabulary/games/sessions", response_model=GameSessionResponse)
async def create_game_session(
    payload: GameSessionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).create_game_session(user, payload)


@router.post("/vocabulary/games/sessions/{session_id}/answers", response_model=GameAnswerResponse)
async def submit_game_answer(
    session_id: str,
    payload: GameAnswerCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).submit_game_answer(user, session_id, payload)


@router.post("/vocabulary/games/sessions/{session_id}/complete", response_model=GameSessionResponse)
async def complete_game_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).complete_game_session(user, session_id)


# --------------------------------------------------------------------------
# Vocabulary — detail. Catch-all single segment, MUST be registered last
# among the /vocabulary/* routes.
# --------------------------------------------------------------------------

@router.get("/vocabulary/{vocabulary_id}", response_model=VocabularyDetailResponse)
async def get_vocabulary_detail(
    vocabulary_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VocabularyService(db).get_vocabulary_detail(user, vocabulary_id)


# --------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------

@router.get("/writing", response_model=list[WritingResponse])
async def list_writing(
    response: Response,
    category: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await CommunicationService(db).list_writing(
        user.id, category=category, limit=limit, offset=offset
    )
    response.headers["X-Total-Count"] = str(total)
    return items


@router.get("/writing/categories", response_model=list[str])
async def list_writing_categories(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).list_writing_categories(user.id)


@router.post("/writing/categories", response_model=list[str], status_code=status.HTTP_201_CREATED)
async def create_writing_category(
    data: WritingCategoryCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await CommunicationService(db).create_writing_category(user.id, data.name)
    return await CommunicationService(db).list_writing_categories(user.id)


@router.post("/writing", response_model=WritingResponse, status_code=status.HTTP_201_CREATED)
async def create_writing(
    data: WritingCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).create_writing(user.id, data)


@router.get("/writing/{item_id}", response_model=WritingResponse)
async def get_writing(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).get_writing(user.id, item_id)


@router.patch("/writing/{item_id}", response_model=WritingResponse)
async def update_writing(
    item_id: str,
    data: WritingUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).update_writing(user.id, item_id, data)


@router.delete("/writing/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_writing(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await CommunicationService(db).delete_writing(user.id, item_id)


@router.post("/writing/{item_id}/ai-feedback", response_model=WritingEvaluationResponse)
async def evaluate_writing(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).evaluate_writing(user.id, item_id)


@router.get("/writing/{item_id}/ai-feedback", response_model=WritingEvaluationResponse)
async def get_writing_feedback(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).get_writing_feedback(user.id, item_id)


@router.post("/writing/{item_id}/ai-rewrite", response_model=WritingRewriteResponse)
async def request_writing_rewrite(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).request_writing_rewrite(user.id, item_id)


@router.get("/writing/{item_id}/ai-rewrite", response_model=WritingRewriteResponse)
async def get_writing_rewrite(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).get_writing_rewrite(user.id, item_id)


# --------------------------------------------------------------------------
# Speaking
# --------------------------------------------------------------------------

@router.get("/speaking", response_model=list[SpeakingResponse])
async def list_speaking(
    response: Response,
    category: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await CommunicationService(db).list_speaking(
        user.id, category=category, limit=limit, offset=offset
    )
    response.headers["X-Total-Count"] = str(total)
    return items


@router.post("/speaking", response_model=SpeakingResponse, status_code=status.HTTP_201_CREATED)
async def create_speaking(
    data: SpeakingCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).create_speaking(user.id, data)


@router.get("/speaking/{item_id}", response_model=SpeakingResponse)
async def get_speaking(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).get_speaking(user.id, item_id)


@router.patch("/speaking/{item_id}", response_model=SpeakingResponse)
async def update_speaking(
    item_id: str,
    data: SpeakingUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await CommunicationService(db).update_speaking(user.id, item_id, data)


@router.delete("/speaking/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_speaking(
    item_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await CommunicationService(db).delete_speaking(user.id, item_id)
