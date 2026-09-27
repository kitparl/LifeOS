"""Per-user progress rules (pure). No progress row means "not started".

- Every judged submission counts as an attempt, except Internal Error (the judge's fault):
  that leaves progress untouched.
- The first Accepted marks the problem solved; solved never regresses.
- Best submission = the Accepted one with the lowest runtime; ties keep the earlier one.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from app.modules.dsa.judge.verdict import Verdict

ATTEMPTED = "attempted"
SOLVED = "solved"


@dataclass(frozen=True)
class SubmissionFacts:
    id: str
    verdict: Verdict
    runtime_ms: int | None
    created_at: datetime


@dataclass(frozen=True)
class ProgressState:
    status: str
    attempt_count: int
    best_submission_id: str | None
    last_attempted_at: datetime | None
    solved_at: datetime | None


def counts_as_attempt(verdict: Verdict) -> bool:
    return verdict != Verdict.INTERNAL_ERROR


def is_better(candidate: SubmissionFacts, best: SubmissionFacts | None) -> bool:
    if candidate.verdict != Verdict.ACCEPTED:
        return False
    if best is None:
        return True
    cand_rt = candidate.runtime_ms if candidate.runtime_ms is not None else float("inf")
    best_rt = best.runtime_ms if best.runtime_ms is not None else float("inf")
    return cand_rt < best_rt or (cand_rt == best_rt and candidate.created_at < best.created_at)


def apply_verdict(
    current: ProgressState | None, submission: SubmissionFacts, best: SubmissionFacts | None
) -> ProgressState | None:
    """New progress after `submission` is judged; None when there is (still) nothing to record."""
    if not counts_as_attempt(submission.verdict):
        return current
    state = current or ProgressState(ATTEMPTED, 0, None, None, None)
    accepted = submission.verdict == Verdict.ACCEPTED
    return replace(
        state,
        status=SOLVED if accepted or state.status == SOLVED else ATTEMPTED,
        attempt_count=state.attempt_count + 1,
        best_submission_id=submission.id if is_better(submission, best) else state.best_submission_id,
        last_attempted_at=max(filter(None, [state.last_attempted_at, submission.created_at])),
        solved_at=state.solved_at or (submission.created_at if accepted else None),
    )
