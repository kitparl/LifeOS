"""Queue job handlers: judge a persisted submission or an in-memory Run job.

Each job opens its own short DB sessions (never a request session) and releases the session
while the sandbox runs. Every failure path records a verdict: nothing is left half-done and
nothing fails open (an unreachable judge is Internal Error, never Accepted).
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import replace

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.dsa.content.references import find_reference, reference_program
from app.modules.dsa.judge.client import JudgeUnavailableError
from app.modules.dsa.judge.queue import RunJob
from app.modules.dsa.judge.runner import Limits, Runner, per_test_limit_ms
from app.modules.dsa.judge.signature import ClassSpec, FunctionSpec, SignatureError, parse_spec, validate_expected
from app.modules.dsa.judge.verdict import (
    CompileOutcome,
    Grading,
    JudgeOutcome,
    RunOutcome,
    Verdict,
    decide,
    internal_error,
)
from app.modules.dsa.models import DsaSubmission, DsaTestCase
from app.modules.dsa.progress import ProgressState, SubmissionFacts, apply_verdict
from app.modules.dsa.repository import UNFINISHED, CatalogRepository, SubmissionRepository

logger = logging.getLogger(__name__)

MAX_STORED_OUTPUT_BYTES = 64 * 1024
NO_REFERENCE = "No reference solution for this problem, so this case isn't checked."
REFERENCE_FAILED = "Couldn't compute the expected output for this input (it may be outside the constraints)."


class JudgeWorker:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], runner: Runner):
        self._sessions = session_factory
        self._runner = runner
        # Recording a verdict reads then writes the user's progress row. Two workers finishing submissions
        # for the same user and problem would both insert it (unique violation: the verdict is rolled back
        # and the submission stays "running") or lose an attempt count. These writes are short; serialize them.
        self._finish_lock = asyncio.Lock()

    async def load_unfinished(self) -> list[str]:
        async with self._sessions() as db:
            ids = await SubmissionRepository(db).claim_unfinished()
            await db.commit()
        if ids:
            logger.info("dsa: re-queued %d unfinished submission(s)", len(ids))
        return ids

    async def judge_run(self, job: RunJob) -> None:
        job.status = "running"
        raw, (expected, unchecked) = await asyncio.gather(
            self._execute(job.language, job.spec, job.code, job.grading.inputs, job.limits),
            self._reference_expected(job),
        )
        job.grading = replace(job.grading, expected=[expected.get(i, e) for i, e in enumerate(job.grading.expected)])
        job.unchecked = unchecked
        job.outcome = raw if isinstance(raw, JudgeOutcome) else self._decide(raw, job.grading)
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

        async with self._finish_lock, self._sessions() as db:
            submissions = SubmissionRepository(db)
            submission = await submissions.get_for_judging(submission_id)
            if submission is None:
                return
            status = "error" if outcome.verdict == Verdict.INTERNAL_ERROR else "done"
            await submissions.finish(submission, outcome, status=status, failed_test=failed_test(outcome, tests))
            await self._update_progress(submissions, submission, outcome)
            await db.commit()

    async def _reference_expected(self, job: RunJob) -> tuple[dict[int, object], dict[int, str]]:
        """Expected outputs for the Run's custom cases from the reference solution, and why any are missing.

        Never raises: a reference that can't run leaves those cases unchecked, it never fails the Run.
        """
        indices = [i for i, custom in enumerate(job.custom) if custom]
        if not indices:
            return {}, {}
        try:
            # The first lookup imports every content source; keep it off the event loop.
            reference = await asyncio.to_thread(find_reference, job.slug, job.spec)
            if reference is None:
                return {}, dict.fromkeys(indices, NO_REFERENCE)
            inputs = [job.grading.inputs[i] for i in indices]
            run = await self._runner.run_reference(reference_program(reference, job.spec), inputs, job.limits)
        except Exception:
            logger.exception("dsa: reference run failed")
            return {}, dict.fromkeys(indices, REFERENCE_FAILED)
        outputs = {c.index: c.out for c in run.cases if c.ok}
        spec = parse_spec(job.spec)
        expected: dict[int, object] = {}
        for k, i in enumerate(indices):
            if k in outputs and _fits_signature(spec, outputs[k], job.grading.inputs[i]):
                expected[i] = outputs[k]
        return expected, {i: REFERENCE_FAILED for i in indices if i not in expected}

    async def _grade(self, language: str, spec: dict, code: str, grading: Grading, limits: Limits) -> JudgeOutcome:
        raw = await self._execute(language, spec, code, grading.inputs, limits)
        return raw if isinstance(raw, JudgeOutcome) else self._decide(raw, grading)

    async def _execute(
        self, language: str, spec: dict, code: str, inputs: list[object], limits: Limits
    ) -> tuple[CompileOutcome | None, RunOutcome | None] | JudgeOutcome:
        """Run the user's program; a judge failure comes back as an Internal Error outcome."""
        try:
            return await self._runner.run(language, spec, code, inputs, limits)
        except JudgeUnavailableError:
            return internal_error(len(inputs), "The judge is unavailable. Please try again shortly.")
        except Exception:
            logger.exception("dsa: unexpected judge failure")
            return internal_error(len(inputs), "Unexpected judge failure.")

    @staticmethod
    def _decide(raw: tuple[CompileOutcome | None, RunOutcome | None], grading: Grading) -> JudgeOutcome:
        # Guarded: an escaping error would leave the job "running" forever
        # (a Run would then block the user's next Run until restart).
        try:
            return decide(*raw, grading)
        except Exception:
            logger.exception("dsa: unexpected judge failure")
            return internal_error(len(grading.inputs), "Unexpected judge failure.")

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


def _fits_signature(spec: FunctionSpec | ClassSpec, output: object, test_input: object) -> bool:
    """The build's rule for trusting a reference output: it must be a valid expected output.

    Outside the constraints a reference can return what the type can't hold (e.g. an int past 2^31).
    """
    try:
        validate_expected(spec, output, test_input)
    except SignatureError:
        return False
    return True


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
