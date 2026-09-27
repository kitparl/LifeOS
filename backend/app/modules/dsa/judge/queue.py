"""In-process judge queue: N asyncio workers, persisted submissions, in-memory Run jobs.

Submissions live in the DB (status pending/running/done/error); unfinished ones are re-queued on
start. Run jobs are ephemeral: kept in memory for RUN_TTL_SECONDS, one active run per user. The
deployed shape is a single uvicorn worker (same assumption as core/rate_limit.py).
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Literal

from app.modules.dsa.judge.runner import Limits
from app.modules.dsa.judge.verdict import Grading, JudgeOutcome

logger = logging.getLogger(__name__)

RUN_TTL_SECONDS = 600


@dataclass
class RunJob:
    user_id: str
    language: str
    code: str
    spec: dict
    grading: Grading
    limits: Limits
    sample_count: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: Literal["pending", "running", "done", "error"] = "pending"
    outcome: JudgeOutcome | None = None
    created_at: float = field(default_factory=time.monotonic)

    @property
    def finished(self) -> bool:
        return self.status in ("done", "error")


SubmissionHandler = Callable[[str], Awaitable[None]]
RunHandler = Callable[[RunJob], Awaitable[None]]
UnfinishedLoader = Callable[[], Awaitable[list[str]]]


class JudgeQueue:
    def __init__(
        self,
        concurrency: int,
        handle_submission: SubmissionHandler,
        handle_run: RunHandler,
        load_unfinished: UnfinishedLoader,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._concurrency = concurrency
        self._handle_submission = handle_submission
        self._handle_run = handle_run
        self._load_unfinished = load_unfinished
        self._clock = clock
        self._queue: asyncio.Queue[tuple[str, str | RunJob]] = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._runs: dict[str, RunJob] = {}

    async def start(self) -> None:
        for submission_id in await self._load_unfinished():
            self._queue.put_nowait(("submission", submission_id))
        self._workers = [asyncio.create_task(self._work(), name=f"dsa-judge-{i}") for i in range(self._concurrency)]

    async def stop(self) -> None:
        for task in self._workers:
            task.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers = []

    async def drain(self) -> None:
        """Wait until every queued job is processed (tests)."""
        await self._queue.join()

    def enqueue_submission(self, submission_id: str) -> None:
        self._queue.put_nowait(("submission", submission_id))

    def enqueue_run(self, job: RunJob) -> None:
        self._purge_expired()
        self._runs[job.id] = job
        self._queue.put_nowait(("run", job))

    def get_run(self, user_id: str, run_id: str) -> RunJob | None:
        job = self._runs.get(run_id)
        return job if job is not None and job.user_id == user_id else None

    def has_active_run(self, user_id: str) -> bool:
        return any(j.user_id == user_id and not j.finished for j in self._runs.values())

    def _purge_expired(self) -> None:
        cutoff = self._clock() - RUN_TTL_SECONDS
        for run_id in [k for k, j in self._runs.items() if j.finished and j.created_at < cutoff]:
            del self._runs[run_id]

    async def _work(self) -> None:
        while True:
            kind, payload = await self._queue.get()
            try:
                if kind == "submission":
                    await self._handle_submission(payload)  # type: ignore[arg-type]
                else:
                    await self._handle_run(payload)  # type: ignore[arg-type]
            except asyncio.CancelledError:
                raise
            except Exception:
                # Handlers record failures themselves; this only guards the worker loop.
                logger.exception("dsa judge job failed (%s)", kind)
            finally:
                self._queue.task_done()
