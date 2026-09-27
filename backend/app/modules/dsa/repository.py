"""DSA queries.

CatalogRepository reads/writes the global catalog. SubmissionRepository owns per-user data:
every user-facing method takes `user_id` and filters by it (a foreign id simply isn't found).
The `*_for_judging` / `claim_unfinished` methods are for the judge worker only (system context).
"""

from __future__ import annotations

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Pagination, paginate
from app.core.timezone import utc_now
from app.modules.dsa.judge.verdict import JudgeOutcome
from app.modules.dsa.models import DsaPattern, DsaProblem, DsaSubmission, DsaTestCase, DsaUserProgress
from app.modules.dsa.progress import ProgressState

UNFINISHED = ("pending", "running")


class CatalogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_patterns(self) -> list[DsaPattern]:
        result = await self.db.execute(select(DsaPattern).order_by(DsaPattern.display_order))
        return list(result.scalars())

    async def get_pattern(self, slug: str) -> DsaPattern | None:
        result = await self.db.execute(select(DsaPattern).where(DsaPattern.slug == slug))
        return result.scalar_one_or_none()

    async def get_pattern_by_id(self, pattern_id: str) -> DsaPattern | None:
        return await self.db.get(DsaPattern, pattern_id)

    async def list_problems(self, pattern_id: str) -> list[DsaProblem]:
        result = await self.db.execute(
            select(DsaProblem).where(DsaProblem.pattern_id == pattern_id).order_by(DsaProblem.display_order)
        )
        return list(result.scalars())

    async def published_counts(self) -> dict[str, int]:
        result = await self.db.execute(
            select(DsaProblem.pattern_id, func.count())
            .where(DsaProblem.status == "published")
            .group_by(DsaProblem.pattern_id)
        )
        return {pattern_id: int(n) for pattern_id, n in result.all()}

    async def get_problem(self, slug: str) -> DsaProblem | None:
        result = await self.db.execute(select(DsaProblem).where(DsaProblem.slug == slug))
        return result.scalar_one_or_none()

    async def get_problem_by_id(self, problem_id: str) -> DsaProblem | None:
        return await self.db.get(DsaProblem, problem_id)

    async def list_tests(self, problem_id: str, *, samples_only: bool) -> list[DsaTestCase]:
        stmt = select(DsaTestCase).where(DsaTestCase.problem_id == problem_id)
        if samples_only:
            stmt = stmt.where(DsaTestCase.is_sample.is_(True))
        result = await self.db.execute(stmt.order_by(DsaTestCase.position))
        return list(result.scalars())

    async def get_test(self, test_id: str) -> DsaTestCase | None:
        return await self.db.get(DsaTestCase, test_id)

    async def next_test_position(self, problem_id: str) -> int:
        result = await self.db.execute(
            select(func.max(DsaTestCase.position)).where(DsaTestCase.problem_id == problem_id)
        )
        current = result.scalar_one_or_none()
        return 0 if current is None else int(current) + 1

    async def add_test(self, test: DsaTestCase) -> DsaTestCase:
        self.db.add(test)
        await self.db.flush()
        return test

    async def delete_test(self, test: DsaTestCase) -> None:
        await self.db.delete(test)
        await self.db.flush()

    async def replace_tests(self, problem_id: str, tests: list[DsaTestCase]) -> None:
        await self.db.execute(delete(DsaTestCase).where(DsaTestCase.problem_id == problem_id))
        self.db.add_all(tests)
        await self.db.flush()


class SubmissionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------ user-scoped

    async def create(self, user_id: str, problem_id: str, language: str, code: str) -> DsaSubmission:
        submission = DsaSubmission(user_id=user_id, problem_id=problem_id, language=language, code=code)
        self.db.add(submission)
        await self.db.flush()
        return submission

    async def get(self, user_id: str, submission_id: str) -> DsaSubmission | None:
        result = await self.db.execute(
            select(DsaSubmission).where(DsaSubmission.id == submission_id, DsaSubmission.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_for_problem(
        self, user_id: str, problem_id: str, pagination: Pagination
    ) -> tuple[list[DsaSubmission], int]:
        stmt = (
            select(DsaSubmission)
            .where(DsaSubmission.user_id == user_id, DsaSubmission.problem_id == problem_id)
            .order_by(DsaSubmission.created_at.desc())
        )
        return await paginate(self.db, stmt, pagination)

    async def get_progress(self, user_id: str, problem_id: str) -> DsaUserProgress | None:
        result = await self.db.execute(
            select(DsaUserProgress).where(DsaUserProgress.user_id == user_id, DsaUserProgress.problem_id == problem_id)
        )
        return result.scalar_one_or_none()

    async def progress_by_problem(self, user_id: str, problem_ids: list[str]) -> dict[str, str]:
        """{problem_id: status} for problems the user has touched."""
        if not problem_ids:
            return {}
        result = await self.db.execute(
            select(DsaUserProgress.problem_id, DsaUserProgress.status).where(
                DsaUserProgress.user_id == user_id, DsaUserProgress.problem_id.in_(problem_ids)
            )
        )
        return dict(result.all())

    async def progress_counts(self, user_id: str) -> dict[str, dict[str, int]]:
        """{pattern_id: {"solved": n, "attempted": m}} over published problems."""
        result = await self.db.execute(
            select(DsaProblem.pattern_id, DsaUserProgress.status, func.count())
            .join(DsaProblem, DsaProblem.id == DsaUserProgress.problem_id)
            .where(DsaUserProgress.user_id == user_id, DsaProblem.status == "published")
            .group_by(DsaProblem.pattern_id, DsaUserProgress.status)
        )
        counts: dict[str, dict[str, int]] = {}
        for pattern_id, status, n in result.all():
            counts.setdefault(pattern_id, {"solved": 0, "attempted": 0})[status] = int(n)
        return counts

    async def save_progress(self, user_id: str, problem_id: str, state: ProgressState) -> None:
        row = await self.get_progress(user_id, problem_id)
        if row is None:
            row = DsaUserProgress(user_id=user_id, problem_id=problem_id)
            self.db.add(row)
        row.status = state.status
        row.attempt_count = state.attempt_count
        row.best_submission_id = state.best_submission_id
        row.last_attempted_at = state.last_attempted_at
        row.solved_at = state.solved_at
        await self.db.flush()

    # ------------------------------------------------------------------ judge worker (system context)

    async def get_for_judging(self, submission_id: str) -> DsaSubmission | None:
        return await self.db.get(DsaSubmission, submission_id)

    async def mark_running(self, submission: DsaSubmission) -> None:
        submission.status = "running"
        await self.db.flush()

    async def finish(
        self, submission: DsaSubmission, outcome: JudgeOutcome, *, status: str, message: str | None
    ) -> None:
        submission.status = status
        submission.verdict = outcome.verdict.value
        submission.passed = outcome.passed
        submission.total = outcome.total
        submission.runtime_ms = outcome.runtime_ms
        submission.memory_kb = outcome.memory_kb
        submission.failed_case = outcome.failed_case
        submission.message = message
        submission.finished_at = utc_now()
        await self.db.flush()

    async def claim_unfinished(self) -> list[str]:
        """Ids of submissions left pending/running (e.g. by a restart), reset to pending, oldest first."""
        result = await self.db.execute(
            select(DsaSubmission.id).where(DsaSubmission.status.in_(UNFINISHED)).order_by(DsaSubmission.created_at)
        )
        ids = list(result.scalars())
        if ids:
            await self.db.execute(update(DsaSubmission).where(DsaSubmission.id.in_(ids)).values(status="pending"))
        return ids
