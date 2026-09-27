from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_admin_user, get_current_user
from app.core.pagination import Pagination, pagination_params
from app.modules.auth.models import User
from app.modules.dsa import schemas
from app.modules.dsa.runtime import current_queue
from app.modules.dsa.service import DsaCatalogService, DsaJudgeService, DsaNoteService

router = APIRouter(prefix="/dsa", tags=["dsa"])

Slug = Annotated[str, Path(min_length=1, max_length=120, pattern=r"^[a-z0-9][a-z0-9-]*$")]
Id = Annotated[str, Path(min_length=1, max_length=36, pattern=r"^[0-9a-fA-F-]+$")]


def _judge(db: AsyncSession) -> DsaJudgeService:
    return DsaJudgeService(db, current_queue())


# ------------------------------------------------------------------ catalog


@router.get("/me", response_model=schemas.DsaMe)
async def dsa_me(user: User = Depends(get_current_user)):
    return DsaCatalogService.me(user)


@router.get("/patterns", response_model=list[schemas.PatternSummary])
async def list_patterns(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await DsaCatalogService(db).patterns(user.id)


@router.get("/patterns/{slug}", response_model=schemas.PatternDetail)
async def get_pattern(slug: Slug, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await DsaCatalogService(db).pattern_detail(user.id, slug)


@router.get("/problems/{slug}", response_model=schemas.ProblemDetail)
async def get_problem(slug: Slug, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await DsaCatalogService(db).problem(user.id, slug)


# ------------------------------------------------------------------ notes (per user)


@router.get("/patterns/{slug}/note", response_model=schemas.Note)
async def get_pattern_note(slug: Slug, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await DsaNoteService(db).pattern_note(user.id, slug)


@router.put("/patterns/{slug}/note", response_model=schemas.Note)
async def save_pattern_note(
    slug: Slug, body: schemas.NoteWrite, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await DsaNoteService(db).save_pattern_note(user.id, slug, body)


@router.get("/problems/{slug}/note", response_model=schemas.Note)
async def get_problem_note(slug: Slug, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await DsaNoteService(db).problem_note(user.id, slug)


@router.put("/problems/{slug}/note", response_model=schemas.Note)
async def save_problem_note(
    slug: Slug, body: schemas.NoteWrite, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await DsaNoteService(db).save_problem_note(user.id, slug, body)


# ------------------------------------------------------------------ run / submit


@router.post("/problems/{slug}/run", response_model=schemas.JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def run_code(
    slug: Slug, body: schemas.RunRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await _judge(db).start_run(user.id, slug, body)


@router.get("/runs/{run_id}", response_model=schemas.RunResult)
async def get_run(run_id: Id, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return _judge(db).get_run(user.id, run_id)


@router.post("/problems/{slug}/submissions", response_model=schemas.JobAccepted, status_code=status.HTTP_202_ACCEPTED)
async def submit_code(
    slug: Slug, body: schemas.SubmitRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await _judge(db).submit(user.id, slug, body)


@router.get("/problems/{slug}/submissions", response_model=schemas.SubmissionPage)
async def list_submissions(
    slug: Slug,
    pagination: Pagination = Depends(pagination_params),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _judge(db).history(user.id, slug, pagination)


@router.get("/submissions/{submission_id}", response_model=schemas.SubmissionDetail)
async def get_submission(submission_id: Id, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _judge(db).get_submission(user.id, submission_id)


# ------------------------------------------------------------------ admin (is_admin checked server-side)


@router.get("/admin/problems/{slug}", response_model=schemas.AdminProblemDetail)
async def admin_get_problem(
    slug: Slug, _admin: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)
):
    return await DsaCatalogService(db).admin_problem(slug)


@router.put("/admin/problems/{slug}", response_model=schemas.AdminProblemDetail)
async def admin_update_problem(
    slug: Slug,
    body: schemas.ProblemUpdate,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await DsaCatalogService(db).admin_update_problem(admin, slug, body)


@router.post("/admin/problems/{slug}/tests", response_model=schemas.AdminTestCase, status_code=status.HTTP_201_CREATED)
async def admin_add_test(
    slug: Slug,
    body: schemas.CaseWrite,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await DsaCatalogService(db).admin_add_test(admin, slug, body)


@router.put("/admin/tests/{test_id}", response_model=schemas.AdminTestCase)
async def admin_update_test(
    test_id: Id,
    body: schemas.CaseWrite,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await DsaCatalogService(db).admin_update_test(admin, test_id, body)


@router.delete("/admin/tests/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_test(
    test_id: Id, admin: User = Depends(get_current_admin_user), db: AsyncSession = Depends(get_db)
):
    await DsaCatalogService(db).admin_delete_test(admin, test_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
