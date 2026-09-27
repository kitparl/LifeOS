from datetime import datetime, timedelta, timezone

from app.modules.dsa.judge.verdict import Verdict
from app.modules.dsa.progress import SOLVED, ProgressState, SubmissionFacts, apply_verdict, is_better
from hypothesis import given
from hypothesis import strategies as st

T0 = datetime(2026, 9, 26, tzinfo=timezone.utc)


def _sub(i: int, verdict: Verdict, runtime: int | None = 10) -> SubmissionFacts:
    return SubmissionFacts(f"s{i}", verdict, runtime, T0 + timedelta(minutes=i))


def test_first_attempt_wrong_answer():
    state = apply_verdict(None, _sub(1, Verdict.WRONG_ANSWER), None)
    assert state == ProgressState("attempted", 1, None, T0 + timedelta(minutes=1), None)


def test_accepted_marks_solved_and_best():
    state = apply_verdict(None, _sub(1, Verdict.ACCEPTED), None)
    assert state.status == SOLVED and state.best_submission_id == "s1" and state.solved_at == T0 + timedelta(minutes=1)


def test_solved_never_regresses_and_keeps_solved_at():
    solved = apply_verdict(None, _sub(1, Verdict.ACCEPTED), None)
    later = apply_verdict(solved, _sub(2, Verdict.WRONG_ANSWER), _sub(1, Verdict.ACCEPTED))
    assert later.status == SOLVED and later.solved_at == solved.solved_at and later.attempt_count == 2
    assert later.best_submission_id == "s1"


def test_faster_accepted_becomes_best_and_ties_keep_earlier():
    best = _sub(1, Verdict.ACCEPTED, runtime=50)
    assert is_better(_sub(2, Verdict.ACCEPTED, runtime=40), best)
    assert not is_better(_sub(2, Verdict.ACCEPTED, runtime=50), best)
    assert not is_better(_sub(2, Verdict.WRONG_ANSWER, runtime=1), best)


def test_internal_error_changes_nothing():
    assert apply_verdict(None, _sub(1, Verdict.INTERNAL_ERROR), None) is None
    state = apply_verdict(None, _sub(1, Verdict.WRONG_ANSWER), None)
    assert apply_verdict(state, _sub(2, Verdict.INTERNAL_ERROR), None) is state


# PBT-03: invariants over any verdict sequence
@given(st.lists(st.tuples(st.sampled_from(list(Verdict)), st.integers(0, 100)), max_size=30))
def test_progress_invariants(events):
    state: ProgressState | None = None
    best: SubmissionFacts | None = None
    ever_solved = False
    attempts = 0
    for i, (verdict, runtime) in enumerate(events):
        sub = _sub(i, verdict, runtime)
        previous = state
        state = apply_verdict(state, sub, best)
        if state is not None and state.best_submission_id == sub.id:
            best = sub
        if verdict != Verdict.INTERNAL_ERROR:
            attempts += 1
        ever_solved = ever_solved or verdict == Verdict.ACCEPTED
        if previous is not None and previous.status == SOLVED:
            assert state.status == SOLVED  # never regresses
        if previous is not None:
            assert state.attempt_count >= previous.attempt_count  # monotonic
    if state is not None:
        assert state.attempt_count == attempts
        assert (state.status == SOLVED) == ever_solved
        assert (state.best_submission_id is None) == (not ever_solved)
