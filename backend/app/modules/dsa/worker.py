"""Queue job handlers: judge a persisted submission or an in-memory Run job.

Each job opens its own short DB sessions (never a request session) and releases the session
while the sandbox runs. Every failure path records a verdict: nothing is left half-done and
nothing fails open (an unreachable judge is Internal Error, never Accepted).
"""

from __future__ import annotations

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.dsa.judge.client import JudgeUnavailableError
from app.modules.dsa.judge.queue import RunJob
from app.modules.dsa.judge.runner import Limits, Runner, per_test_limit_ms
from app.modules.dsa.judge.verdict import Grading, JudgeOutcome, Verdict, decide, internal_error
from app.modules.dsa.models import DsaSubmission, DsaTestCase
from app.modules.dsa.progress import ProgressState, SubmissionFacts, apply_verdict
from app.modules.dsa.repository import UNFINISHED, CatalogRepository, SubmissionRepository

logger = logging.getLogger(__name__)

MAX_STORED_OUTPUT_BYTES = 64 * 1024


class JudgeWorker:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], runner: Runner):
        self._sessions = session_factory
        self._runner = runner

    async def load_unfinished(self) -> list[str]:
        async with self._sessions() as db:
            ids = await SubmissionRepository(db).claim_unfinished()
            await db.commit()
        if ids:
            logger.info("dsa: re-queued %d unfinished submission(s)", len(ids))
        return ids

    async def judge_run(self, job: RunJob) -> None:
        job.status = "running"
        job.outcome = await self._grade(job.language, job.spec, job.code, job.grading, job.limits)
        job.status = "error" if job.outcome.verdict == Verdict.INTERNAL_ERROR else "done"

    async def judge_submission(self, submission_id: str) -> None:
        async with self._sessions() as db:
            submissions = SubmissionRepository(db)
            submission = await submissions.get_for_judging(submission_id)
            if submission is None or submission.status not in UNFINISHED:
                return
            catalog = CatalogRepository(db)
            problem = await catalog.get_problem_by_id(submission.problem_id)
            tests = await catalog.list_tests(submission.problem_id, samples_only=False) if problem else []
            await submissions.mark_running(submission)
            await db.commit()
            language, code = submission.language, submission.code

        if problem is None or problem.signature is None or not tests:
            outcome = internal_error(len(tests), "problem is not judgeable")
        else:
            limits = Limits(problem.time_limit_ms, problem.memory_limit_mb)
            grading = Grading(
                inputs=[t.input for t in tests],
                expected=[t.expected for t in tests],
                per_test_limit_ms=per_test_limit_ms(language, limits),
                compare_mode=problem.compare_mode,
                checker=problem.checker,
            )
            outcome = await self._grade(language, problem.signature, code, grading, limits)

        async with self._sessions() as db:
            submissions = SubmissionRepository(db)
            submission = await submissions.get_for_judging(submission_id)
            if submission is None:
                return
            status = "error" if outcome.verdict == Verdict.INTERNAL_ERROR else "done"
            await submissions.finish(submission, outcome, status=status, failed_test=failed_test(outcome, tests))
            await self._update_progress(submissions, submission, outcome)
            await db.commit()

    async def _grade(self, language: str, spec: dict, code: str, grading: Grading, limits: Limits) -> JudgeOutcome:
        try:
            compiled, run = await self._runner.run(language, spec, code, grading.inputs, limits)
        except JudgeUnavailableError:
            return internal_error(len(grading.inputs), "The judge is unavailable. Please try again shortly.")
        except Exception:
            logger.exception("dsa: unexpected judge failure")
            return internal_error(len(grading.inputs), "Unexpected judge failure.")
        return decide(compiled, run, grading)

    @staticmethod
    async def _update_progress(
        submissions: SubmissionRepository, submission: DsaSubmission, outcome: JudgeOutcome
    ) -> None:
        row = await submissions.get_progress(submission.user_id, submission.problem_id)
        current = (
            ProgressState(row.status, row.attempt_count, row.best_submission_id, row.last_attempted_at, row.solved_at)
            if row is not None
            else None
        )
        best = None
        if row is not None and row.best_submission_id:
            best_row = await submissions.get_for_judging(row.best_submission_id)
            if best_row is not None and best_row.verdict is not None:
                best = SubmissionFacts(best_row.id, Verdict(best_row.verdict), best_row.runtime_ms, best_row.created_at)
        facts = SubmissionFacts(submission.id, outcome.verdict, outcome.runtime_ms, submission.created_at)
        new_state = apply_verdict(current, facts, best)
        if new_state is not None and new_state != current:
            await submissions.save_progress(submission.user_id, submission.problem_id, new_state)


def failed_test(outcome: JudgeOutcome, tests: list[DsaTestCase]) -> dict | None:
    """Snapshot of the first failing test, so the result still reads right if the test is edited later.

    `answered` is false when the program stopped on this test without a result line (TLE, MLE, crash);
    the outcome message then says why. An oversized output is replaced by a note instead of stored.
    """
    if outcome.failed_case is None:
        return None
    index = outcome.failed_case - 1
    test = tests[index]
    report = next((c for c in outcome.cases if c.index == index), None)
    actual = report.actual if report else None
    error = report.error if report else None
    if actual is not None and len(json.dumps(actual, separators=(",", ":"))) > MAX_STORED_OUTPUT_BYTES:
        actual, error = None, f"Your output is larger than {MAX_STORED_OUTPUT_BYTES // 1024} KB, so it isn't shown."
    return {
        "input": test.input,
        "expected": test.expected,
        "actual": actual,
        "error": error,
        "answered": report is not None,
        "is_sample": test.is_sample,
    }
