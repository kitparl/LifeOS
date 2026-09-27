"""DSA services: catalog reads, admin edits, and Run/Submit orchestration (judging happens in worker.py)."""

from __future__ import annotations

import logging

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
    TooManyRequestsError,
)
from app.core.pagination import Pagination
from app.core.rate_limit import SlidingWindowLimiter
from app.modules.auth.models import User
from app.modules.dsa import schemas
from app.modules.dsa.judge import drivers
from app.modules.dsa.judge.compare import CHECKERS
from app.modules.dsa.judge.languages import LANGUAGE_IDS
from app.modules.dsa.judge.queue import JudgeQueue, RunJob
from app.modules.dsa.judge.runner import Limits, per_test_limit_ms
from app.modules.dsa.judge.signature import SignatureError, parse_spec, validate_expected, validate_input
from app.modules.dsa.judge.verdict import Grading
from app.modules.dsa.models import DsaNote, DsaPattern, DsaProblem, DsaSubmission, DsaTestCase
from app.modules.dsa.repository import CatalogRepository, NoteRepository, SubmissionRepository

logger = logging.getLogger(__name__)

_run_limiter: SlidingWindowLimiter | None = None
_submit_limiter: SlidingWindowLimiter | None = None


def reset_limiters() -> None:
    """Forget rate-limit history (tests; settings changes)."""
    global _run_limiter, _submit_limiter
    _run_limiter = _submit_limiter = None


def _limiters(settings: Settings) -> tuple[SlidingWindowLimiter, SlidingWindowLimiter]:
    global _run_limiter, _submit_limiter
    if _run_limiter is None or _submit_limiter is None:
        _run_limiter = SlidingWindowLimiter(settings.dsa_run_per_minute, 60)
        _submit_limiter = SlidingWindowLimiter(settings.dsa_submit_per_minute, 60)
    return _run_limiter, _submit_limiter


def _starters(signature: dict | None) -> dict[str, str]:
    if signature is None:
        return {}
    return {lang: drivers.starter(lang, signature) for lang in LANGUAGE_IDS}


def _to_detail(
    problem: DsaProblem, pattern: DsaPattern, samples: list[DsaTestCase], progress: str
) -> schemas.ProblemDetail:
    return schemas.ProblemDetail(
        slug=problem.slug,
        title=problem.title,
        difficulty=problem.difficulty,
        tags=problem.tags,
        is_variant=problem.is_variant,
        status=problem.status,
        pattern_slug=pattern.slug,
        pattern_name=pattern.name,
        statement=problem.statement,
        constraints=problem.constraints,
        signature=problem.signature,
        time_limit_ms=problem.time_limit_ms,
        memory_limit_mb=problem.memory_limit_mb,
        samples=[schemas.SampleCase(input=t.input, expected=t.expected, explanation=t.explanation) for t in samples],
        starter_code=_starters(problem.signature) if problem.status == "published" else {},
        languages=list(LANGUAGE_IDS) if problem.status == "published" else [],
        progress=progress,
    )


def _admin_test(test: DsaTestCase) -> schemas.AdminTestCase:
    return schemas.AdminTestCase(
        id=test.id,
        position=test.position,
        input=test.input,
        expected=test.expected,
        is_sample=test.is_sample,
        kind=test.kind,
        explanation=test.explanation,
    )


class DsaCatalogService:
    def __init__(self, db: AsyncSession):
        self.catalog = CatalogRepository(db)
        self.submissions = SubmissionRepository(db)

    @staticmethod
    def me(user: User) -> schemas.DsaMe:
        return schemas.DsaMe(can_edit=bool(user.is_admin))

    async def patterns(self, user_id: str) -> list[schemas.PatternSummary]:
        patterns = await self.catalog.list_patterns()
        totals = await self.catalog.published_counts()
        progress = await self.submissions.progress_counts(user_id)
        return [self._summary(p, totals.get(p.id, 0), progress.get(p.id, {})) for p in patterns]

    async def pattern_detail(self, user_id: str, slug: str) -> schemas.PatternDetail:
        pattern = await self.catalog.get_pattern(slug)
        if pattern is None:
            raise NotFoundError("Pattern not found")
        problems = await self.catalog.list_problems(pattern.id)
        statuses = await self.submissions.progress_by_problem(user_id, [p.id for p in problems])
        published = [p for p in problems if p.status == "published"]
        counts = {"solved": 0, "attempted": 0}
        for p in published:
            if p.id in statuses:
                counts[statuses[p.id]] += 1
        rows = [
            schemas.ProblemRow(
                slug=p.slug,
                title=p.title,
                difficulty=p.difficulty,
                tags=p.tags,
                is_variant=p.is_variant,
                status=p.status,
                progress=statuses.get(p.id, "not_started"),
            )
            for p in problems
        ]
        return schemas.PatternDetail(**self._summary(pattern, len(published), counts).model_dump(), problems=rows)

    @staticmethod
    def _summary(pattern: DsaPattern, total: int, counts: dict[str, int]) -> schemas.PatternSummary:
        return schemas.PatternSummary(
            slug=pattern.slug,
            number=pattern.number,
            name=pattern.name,
            description=pattern.description,
            week=pattern.week,
            total=total,
            solved=counts.get("solved", 0),
            attempted=counts.get("attempted", 0),
        )

    async def problem(self, user_id: str, slug: str) -> schemas.ProblemDetail:
        problem, pattern = await self._problem_and_pattern(slug)
        samples = await self.catalog.list_tests(problem.id, samples_only=True) if problem.status == "published" else []
        progress = await self.submissions.progress_by_problem(user_id, [problem.id])
        return _to_detail(problem, pattern, samples, progress.get(problem.id, "not_started"))

    async def _problem_and_pattern(self, slug: str) -> tuple[DsaProblem, DsaPattern]:
        problem = await self.catalog.get_problem(slug)
        if problem is None:
            raise NotFoundError("Problem not found")
        pattern = await self.catalog.get_pattern_by_id(problem.pattern_id)
        assert pattern is not None  # FK
        return problem, pattern

    # ------------------------------------------------------------------ admin

    async def admin_problem(self, slug: str) -> schemas.AdminProblemDetail:
        problem, pattern = await self._problem_and_pattern(slug)
        tests = await self.catalog.list_tests(problem.id, samples_only=False)
        detail = _to_detail(problem, pattern, [t for t in tests if t.is_sample], "not_started")
        return schemas.AdminProblemDetail(
            **detail.model_dump(),
            compare_mode=problem.compare_mode,
            checker=problem.checker,
            edited_in_ui=problem.edited_in_ui,
            tests=[_admin_test(t) for t in tests],
        )

    async def admin_update_problem(
        self, actor: User, slug: str, data: schemas.ProblemUpdate
    ) -> schemas.AdminProblemDetail:
        problem, _ = await self._problem_and_pattern(slug)
        changes = data.model_dump(exclude_unset=True)
        if changes.get("signature") is not None:
            changes["signature"] = _checked_signature(changes["signature"])
        signature = changes.get("signature", problem.signature)
        mode = changes.get("compare_mode", problem.compare_mode)
        checker = changes.get("checker", problem.checker)
        if mode == "checker" and checker not in CHECKERS:
            raise BadRequestError(f"Unknown checker {checker!r}")
        tests = await self.catalog.list_tests(problem.id, samples_only=False)
        if "signature" in changes and signature is not None:
            _check_tests(signature, tests)
        if changes.get("status", problem.status) == "published":
            if signature is None:
                raise BadRequestError("A published problem needs a signature")
            if not any(t.is_sample for t in tests):
                raise BadRequestError("A published problem needs at least one sample test")
        before = {k: getattr(problem, k) for k in changes}
        for key, value in changes.items():
            setattr(problem, key, value)
        self._mark_edited(problem, actor)
        _audit(actor, "update_problem", problem.slug, before, changes)
        return await self.admin_problem(slug)

    async def admin_add_test(self, actor: User, slug: str, data: schemas.CaseWrite) -> schemas.AdminTestCase:
        problem, _ = await self._problem_and_pattern(slug)
        self._validate_case(problem, data)
        position = data.position if data.position is not None else await self.catalog.next_test_position(problem.id)
        test = DsaTestCase(
            problem_id=problem.id,
            position=position,
            input=data.input,
            expected=data.expected,
            is_sample=data.is_sample,
            kind="manual",
            explanation=data.explanation if data.is_sample else None,
        )
        try:
            await self.catalog.add_test(test)
        except IntegrityError as exc:  # unique (problem_id, position)
            raise ConflictError("A test already exists at that position") from exc
        self._mark_edited(problem, actor)
        _audit(actor, "add_test", problem.slug, {}, {"position": position, "is_sample": data.is_sample})
        return _admin_test(test)

    async def admin_update_test(self, actor: User, test_id: str, data: schemas.CaseWrite) -> schemas.AdminTestCase:
        test = await self.catalog.get_test(test_id)
        if test is None:
            raise NotFoundError("Test case not found")
        problem = await self.catalog.get_problem_by_id(test.problem_id)
        assert problem is not None
        self._validate_case(problem, data)
        before = {"is_sample": test.is_sample, "position": test.position}
        test.input, test.expected, test.is_sample = data.input, data.expected, data.is_sample
        test.explanation = data.explanation if data.is_sample else None
        if data.position is not None:
            test.position = data.position
        self._mark_edited(problem, actor)
        _audit(actor, "update_test", problem.slug, before, {"is_sample": test.is_sample, "position": test.position})
        return _admin_test(test)

    async def admin_delete_test(self, actor: User, test_id: str) -> None:
        test = await self.catalog.get_test(test_id)
        if test is None:
            raise NotFoundError("Test case not found")
        problem = await self.catalog.get_problem_by_id(test.problem_id)
        assert problem is not None
        await self.catalog.delete_test(test)
        self._mark_edited(problem, actor)
        _audit(actor, "delete_test", problem.slug, {"position": test.position}, {})

    @staticmethod
    def _validate_case(problem: DsaProblem, data: schemas.CaseWrite) -> None:
        if problem.signature is None:
            raise BadRequestError("Set the problem's signature before adding tests")
        spec = parse_spec(problem.signature)
        try:
            validate_input(spec, data.input)
            validate_expected(spec, data.expected, data.input)
        except SignatureError as exc:
            raise BadRequestError(str(exc)) from exc

    @staticmethod
    def _mark_edited(problem: DsaProblem, actor: User) -> None:
        problem.edited_in_ui = True
        problem.updated_by = actor.id


def _checked_signature(signature: dict) -> dict:
    try:
        return parse_spec(signature).model_dump(exclude_none=True)
    except ValidationError as exc:
        raise BadRequestError(f"Invalid signature: {exc.errors()[0]['msg']}") from exc


def _check_tests(signature: dict, tests: list[DsaTestCase]) -> None:
    spec = parse_spec(signature)
    for test in tests:
        try:
            validate_input(spec, test.input)
            validate_expected(spec, test.expected, test.input)
        except SignatureError as exc:
            raise BadRequestError(f"Test #{test.position} does not match the new signature: {exc}") from exc


def _audit(actor: User, action: str, problem_slug: str, before: dict, after: dict) -> None:
    """Admin catalog changes (SECURITY-13). Long text fields are logged by length only."""

    def brief(values: dict) -> dict:
        return {
            k: (f"<{len(v)} chars>" if isinstance(v, str) and len(v) > 80 else v)
            for k, v in values.items()
            if k != "signature"
        }

    logger.info(
        "dsa.admin action=%s actor=%s problem=%s before=%s after=%s signature_changed=%s",
        action,
        actor.id,
        problem_slug,
        brief(before),
        brief(after),
        "signature" in after,
    )


class DsaNoteService:
    """A user's private notes on patterns and problems (drafts included: notes don't need content)."""

    def __init__(self, db: AsyncSession):
        self.catalog = CatalogRepository(db)
        self.notes = NoteRepository(db)

    async def pattern_note(self, user_id: str, slug: str) -> schemas.Note:
        pattern = await self._pattern(slug)
        return _to_note(await self.notes.get(user_id, pattern_id=pattern.id))

    async def save_pattern_note(self, user_id: str, slug: str, body: schemas.NoteWrite) -> schemas.Note:
        pattern = await self._pattern(slug)
        return _to_note(await self.notes.save(user_id, body.content, pattern_id=pattern.id))

    async def problem_note(self, user_id: str, slug: str) -> schemas.Note:
        problem = await self._problem(slug)
        return _to_note(await self.notes.get(user_id, problem_id=problem.id))

    async def save_problem_note(self, user_id: str, slug: str, body: schemas.NoteWrite) -> schemas.Note:
        problem = await self._problem(slug)
        return _to_note(await self.notes.save(user_id, body.content, problem_id=problem.id))

    async def _pattern(self, slug: str) -> DsaPattern:
        pattern = await self.catalog.get_pattern(slug)
        if pattern is None:
            raise NotFoundError("Pattern not found")
        return pattern

    async def _problem(self, slug: str) -> DsaProblem:
        problem = await self.catalog.get_problem(slug)
        if problem is None:
            raise NotFoundError("Problem not found")
        return problem


def _to_note(note: DsaNote | None) -> schemas.Note:
    return schemas.Note(content=note.content, updated_at=note.updated_at) if note else schemas.Note(content="")


class DsaJudgeService:
    def __init__(self, db: AsyncSession, queue: JudgeQueue | None, settings: Settings | None = None):
        self.db = db
        self.catalog = CatalogRepository(db)
        self.submissions = SubmissionRepository(db)
        self.queue = queue
        self.settings = settings or get_settings()

    def _require_queue(self) -> JudgeQueue:
        if self.queue is None:
            raise ServiceUnavailableError("The judge is not configured")
        return self.queue

    async def _judgeable(self, slug: str) -> DsaProblem:
        problem = await self.catalog.get_problem(slug)
        if problem is None:
            raise NotFoundError("Problem not found")
        if problem.status != "published" or problem.signature is None:
            raise ConflictError("This problem is not available yet")
        return problem

    async def start_run(self, user_id: str, slug: str, req: schemas.RunRequest) -> schemas.JobAccepted:
        queue = self._require_queue()
        problem = await self._judgeable(slug)
        spec = parse_spec(problem.signature)
        for i, custom in enumerate(req.custom_inputs):
            try:
                validate_input(spec, custom)
            except SignatureError as exc:
                raise BadRequestError(f"Custom input {i + 1}: {exc}") from exc
        if queue.has_active_run(user_id):
            raise ConflictError("A run is already in progress")
        run_limiter, _ = _limiters(self.settings)
        if not run_limiter.hit(user_id):
            raise TooManyRequestsError("Too many runs; wait a moment")
        samples = await self.catalog.list_tests(problem.id, samples_only=True)
        limits = Limits(problem.time_limit_ms, problem.memory_limit_mb)
        grading = Grading(
            inputs=[t.input for t in samples] + list(req.custom_inputs),
            expected=[t.expected for t in samples] + [None] * len(req.custom_inputs),
            per_test_limit_ms=per_test_limit_ms(req.language, limits),
            compare_mode=problem.compare_mode,
            checker=problem.checker,
        )
        job = RunJob(user_id, req.language, req.code, problem.signature, grading, limits, len(samples))
        queue.enqueue_run(job)
        return schemas.JobAccepted(id=job.id, status=job.status)

    def get_run(self, user_id: str, run_id: str) -> schemas.RunResult:
        job = self.queue.get_run(user_id, run_id) if self.queue is not None else None
        if job is None:
            raise NotFoundError("Run not found")
        result = schemas.RunResult(id=job.id, status=job.status)
        outcome = job.outcome
        if outcome is None:
            return result
        g = job.grading
        cases = []
        for report in outcome.cases:
            cases.append(
                schemas.RunCaseResult(
                    index=report.index,
                    input=g.inputs[report.index],
                    expected=g.expected[report.index],
                    actual=report.actual,
                    passed=report.passed,
                    ms=report.ms,
                    error=report.error,
                    is_custom=report.index >= job.sample_count,
                )
            )
        return result.model_copy(
            update={
                "verdict": outcome.verdict.value,
                "message": outcome.message,
                "cases": cases,
                "stdout": outcome.stdout,
                "stderr": outcome.stderr,
            }
        )

    async def submit(self, user_id: str, slug: str, req: schemas.SubmitRequest) -> schemas.JobAccepted:
        queue = self._require_queue()
        problem = await self._judgeable(slug)
        _, submit_limiter = _limiters(self.settings)
        if not submit_limiter.hit(user_id):
            raise TooManyRequestsError("Too many submissions; wait a moment")
        submission = await self.submissions.create(user_id, problem.id, req.language, req.code)
        # Commit before enqueueing so the worker's own session can see the row.
        await self.db.commit()
        queue.enqueue_submission(submission.id)
        return schemas.JobAccepted(id=submission.id, status="pending")

    async def get_submission(self, user_id: str, submission_id: str) -> schemas.SubmissionDetail:
        submission = await self.submissions.get(user_id, submission_id)
        if submission is None:
            raise NotFoundError("Submission not found")
        problem = await self.catalog.get_problem_by_id(submission.problem_id)
        assert problem is not None
        return schemas.SubmissionDetail(
            **_summary(submission).model_dump(),
            problem_slug=problem.slug,
            code=submission.code,
            failed_case=submission.failed_case,
            message=submission.message,
        )

    async def history(self, user_id: str, slug: str, pagination: Pagination) -> schemas.SubmissionPage:
        problem = await self.catalog.get_problem(slug)
        if problem is None:
            raise NotFoundError("Problem not found")
        rows, total = await self.submissions.list_for_problem(user_id, problem.id, pagination)
        return schemas.SubmissionPage(items=[_summary(s) for s in rows], total=total)


def _summary(submission: DsaSubmission) -> schemas.SubmissionSummary:
    return schemas.SubmissionSummary(
        id=submission.id,
        language=submission.language,
        status=submission.status,
        verdict=submission.verdict,
        passed=submission.passed,
        total=submission.total,
        runtime_ms=submission.runtime_ms,
        memory_kb=submission.memory_kb,
        created_at=submission.created_at,
    )
