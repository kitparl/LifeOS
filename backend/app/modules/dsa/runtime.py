"""Process-wide judge queue lifecycle (started from the app lifespan only when the judge is configured)."""

from __future__ import annotations

import logging

from app.core.config import Settings
from app.core.database import async_session_factory
from app.modules.dsa.judge.client import GoJudgeClient
from app.modules.dsa.judge.queue import JudgeQueue
from app.modules.dsa.judge.runner import Runner
from app.modules.dsa.worker import JudgeWorker

logger = logging.getLogger(__name__)

_queue: JudgeQueue | None = None


def current_queue() -> JudgeQueue | None:
    return _queue


def install_queue(queue: JudgeQueue | None) -> None:
    """Set (or clear) the active queue; used by start_judge and by tests."""
    global _queue
    _queue = queue


def build_queue(worker: JudgeWorker, concurrency: int) -> JudgeQueue:
    return JudgeQueue(concurrency, worker.judge_submission, worker.judge_run, worker.load_unfinished)


async def start_judge(settings: Settings) -> None:
    if not settings.dsa_judge_url.strip():
        logger.info("dsa: DSA_JUDGE_URL not set; Run/Submit are disabled")
        return
    client = GoJudgeClient(settings.dsa_judge_url, settings.dsa_judge_token, settings.dsa_judge_timeout_seconds)
    queue = build_queue(JudgeWorker(async_session_factory, Runner(client)), settings.dsa_judge_concurrency)
    await queue.start()
    install_queue(queue)


async def stop_judge() -> None:
    queue = current_queue()
    if queue is not None:
        await queue.stop()
        install_queue(None)
