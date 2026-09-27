"""Turn raw sandbox results into a verdict. Pure logic; the first failing test decides.

A test with no result line is the one running when the sandbox stopped the program, so the
sandbox status explains it (TLE / MLE / crash). Anything unexplained fails closed: never Accepted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.modules.dsa.judge.compare import outputs_match


class Verdict(str, Enum):  # not StrEnum: the backend must run on Python 3.10
    ACCEPTED = "Accepted"
    WRONG_ANSWER = "Wrong Answer"
    TIME_LIMIT = "Time Limit Exceeded"
    MEMORY_LIMIT = "Memory Limit Exceeded"
    RUNTIME_ERROR = "Runtime Error"
    COMPILE_ERROR = "Compilation Error"
    INTERNAL_ERROR = "Internal Error"

    def __str__(self) -> str:
        return self.value  # match StrEnum formatting on every Python version


# go-judge Result.status values
SANDBOX_ACCEPTED = "Accepted"
_SANDBOX_TO_VERDICT = {
    "Time Limit Exceeded": Verdict.TIME_LIMIT,
    "Memory Limit Exceeded": Verdict.MEMORY_LIMIT,
    "Output Limit Exceeded": Verdict.RUNTIME_ERROR,
    "Nonzero Exit Status": Verdict.RUNTIME_ERROR,
    "Signalled": Verdict.RUNTIME_ERROR,
    SANDBOX_ACCEPTED: Verdict.RUNTIME_ERROR,  # exited cleanly before finishing all tests (e.g. sys.exit)
}


@dataclass(frozen=True)
class CaseResult:
    """One `result.jsonl` line."""

    index: int
    ok: bool
    out: object = None
    ms: float = 0.0
    err: str | None = None


@dataclass(frozen=True)
class CompileOutcome:
    ok: bool
    output: str = ""


@dataclass(frozen=True)
class RunOutcome:
    status: str
    time_ms: int = 0
    memory_kb: int = 0
    cases: list[CaseResult] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class CaseReport:
    index: int
    # None when there is no expected output to compare against (custom Run inputs).
    passed: bool | None
    actual: object = None
    ms: float | None = None
    error: str | None = None


@dataclass(frozen=True)
class JudgeOutcome:
    verdict: Verdict
    passed: int
    total: int
    runtime_ms: int | None = None
    memory_kb: int | None = None
    failed_case: int | None = None  # 1-based
    message: str | None = None  # compiler output, runtime error text, or sandbox status
    cases: list[CaseReport] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class Grading:
    """How to judge one job; `expected[i] is None` means "not compared" (custom inputs)."""

    inputs: list[object]
    expected: list[object]
    per_test_limit_ms: float
    compare_mode: str
    checker: str | None = None


def internal_error(total: int, message: str) -> JudgeOutcome:
    return JudgeOutcome(Verdict.INTERNAL_ERROR, passed=0, total=total, message=message)


def decide(compile_outcome: CompileOutcome | None, run: RunOutcome | None, grading: Grading) -> JudgeOutcome:
    total = len(grading.inputs)
    if compile_outcome is not None and not compile_outcome.ok:
        return JudgeOutcome(Verdict.COMPILE_ERROR, passed=0, total=total, message=compile_outcome.output)
    if run is None:
        return internal_error(total, "no run result")
    if run.status not in _SANDBOX_TO_VERDICT:
        return internal_error(total, run.status)

    by_index = {c.index: c for c in run.cases}
    reports: list[CaseReport] = []
    passed = 0
    first_failure: tuple[Verdict, int, str | None] | None = None
    for k in range(total):
        case = by_index.get(k)
        if case is None:
            # The program stopped here: every later test is unreached.
            if first_failure is None:
                first_failure = (_SANDBOX_TO_VERDICT[run.status], k, _stop_reason(run.status))
            break
        verdict, report = _grade_case(case, k, grading)
        reports.append(report)
        if verdict is None:
            passed += report.passed is True
            continue
        if first_failure is None:
            first_failure = (verdict, k, case.err)

    if first_failure is None and run.status != SANDBOX_ACCEPTED:
        first_failure = (_SANDBOX_TO_VERDICT[run.status], total - 1, run.status)

    common = {
        "passed": passed,
        "total": total,
        "memory_kb": run.memory_kb,
        "cases": reports,
        "stdout": run.stdout,
        "stderr": run.stderr,
    }
    if first_failure is not None:
        verdict, index, message = first_failure
        return JudgeOutcome(verdict, failed_case=index + 1, message=message, **common)
    runtime = max((c.ms for c in run.cases), default=0.0)
    return JudgeOutcome(Verdict.ACCEPTED, runtime_ms=round(runtime), **common)


def _stop_reason(status: str) -> str:
    return "exited before finishing all tests" if status == SANDBOX_ACCEPTED else status


def _grade_case(case: CaseResult, k: int, grading: Grading) -> tuple[Verdict | None, CaseReport]:
    if not case.ok:
        return Verdict.RUNTIME_ERROR, CaseReport(k, passed=False, error=case.err)
    if case.ms > grading.per_test_limit_ms:
        return Verdict.TIME_LIMIT, CaseReport(k, passed=False, actual=case.out, ms=case.ms)
    expected = grading.expected[k]
    if expected is None:
        return None, CaseReport(k, passed=None, actual=case.out, ms=case.ms)
    ok = outputs_match(
        grading.compare_mode, expected, case.out, checker_name=grading.checker, test_input=grading.inputs[k]
    )
    report = CaseReport(k, passed=ok, actual=case.out, ms=case.ms)
    return (None if ok else Verdict.WRONG_ANSWER), report
