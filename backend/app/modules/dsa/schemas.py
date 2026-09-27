"""DSA API schemas. All input bounds live here (SECURITY-05)."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.dsa.judge.compare import CompareMode
from app.modules.dsa.judge.languages import LanguageId

Difficulty = Literal["easy", "medium", "hard"]
ProblemStatus = Literal["draft", "published"]
ProgressStatus = Literal["not_started", "attempted", "solved"]
JobStatus = Literal["pending", "running", "done", "error"]
TestKind = Literal["example", "edge", "random", "manual"]

MAX_CODE_CHARS = 64 * 1024
MAX_NOTE_CHARS = 100_000
MAX_CUSTOM_INPUTS = 3
MAX_CUSTOM_INPUT_BYTES = 16 * 1024
MAX_STATEMENT_CHARS = 50_000
MAX_TEST_JSON_BYTES = 256 * 1024


def _json_size(value: object) -> int:
    return len(json.dumps(value, separators=(",", ":")))


# ---------------------------------------------------------------- catalog (read)


class DsaMe(BaseModel):
    can_edit: bool


class PatternSummary(BaseModel):
    slug: str
    number: int
    name: str
    description: str
    week: int
    total: int
    solved: int
    attempted: int


class ProblemRow(BaseModel):
    slug: str
    title: str
    difficulty: Difficulty
    tags: list[str]
    is_variant: bool
    status: ProblemStatus
    progress: ProgressStatus


class PatternDetail(PatternSummary):
    problems: list[ProblemRow]


class SampleCase(BaseModel):
    input: Any
    expected: Any
    explanation: str | None = None


class ProblemDetail(BaseModel):
    slug: str
    title: str
    difficulty: Difficulty
    tags: list[str]
    is_variant: bool
    status: ProblemStatus
    pattern_slug: str
    pattern_name: str
    statement: str
    constraints: str
    signature: dict | None
    time_limit_ms: int
    memory_limit_mb: int
    samples: list[SampleCase]
    starter_code: dict[str, str]
    languages: list[LanguageId]
    progress: ProgressStatus


# ---------------------------------------------------------------- run / submit


class SubmitRequest(BaseModel):
    language: LanguageId
    code: str = Field(min_length=1, max_length=MAX_CODE_CHARS)


class RunRequest(SubmitRequest):
    custom_inputs: list[Any] = Field(default_factory=list, max_length=MAX_CUSTOM_INPUTS)

    @field_validator("custom_inputs")
    @classmethod
    def _bounded(cls, values: list[Any]) -> list[Any]:
        for value in values:
            if _json_size(value) > MAX_CUSTOM_INPUT_BYTES:
                raise ValueError(f"each custom input must be at most {MAX_CUSTOM_INPUT_BYTES} bytes of JSON")
        return values


class JobAccepted(BaseModel):
    id: str
    status: JobStatus


class RunCaseResult(BaseModel):
    index: int
    input: Any
    expected: Any | None
    actual: Any | None
    passed: bool | None
    ms: float | None
    error: str | None
    is_custom: bool


class RunResult(BaseModel):
    id: str
    status: JobStatus
    verdict: str | None = None
    message: str | None = None
    cases: list[RunCaseResult] = Field(default_factory=list)
    stdout: str = ""
    stderr: str = ""


class SubmissionSummary(BaseModel):
    id: str
    language: LanguageId
    status: JobStatus
    verdict: str | None
    passed: int
    total: int
    runtime_ms: int | None
    memory_kb: int | None
    created_at: datetime


class SubmissionDetail(SubmissionSummary):
    problem_slug: str
    code: str
    failed_case: int | None
    message: str | None


class SubmissionPage(BaseModel):
    items: list[SubmissionSummary]
    total: int


# ---------------------------------------------------------------- admin


class AdminTestCase(BaseModel):
    id: str
    position: int
    input: Any
    expected: Any
    is_sample: bool
    kind: TestKind
    explanation: str | None


class AdminProblemDetail(ProblemDetail):
    compare_mode: CompareMode
    checker: str | None
    edited_in_ui: bool
    tests: list[AdminTestCase]


class ProblemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    difficulty: Difficulty | None = None
    tags: list[str] | None = Field(default=None, max_length=10)
    is_variant: bool | None = None
    status: ProblemStatus | None = None
    statement: str | None = Field(default=None, max_length=MAX_STATEMENT_CHARS)
    constraints: str | None = Field(default=None, max_length=MAX_STATEMENT_CHARS)
    signature: dict | None = None
    compare_mode: CompareMode | None = None
    checker: str | None = Field(default=None, max_length=60)
    time_limit_ms: int | None = Field(default=None, ge=100, le=5000)
    memory_limit_mb: int | None = Field(default=None, ge=32, le=512)

    @field_validator("tags")
    @classmethod
    def _tag_bounds(cls, tags: list[str] | None) -> list[str] | None:
        if tags is not None and any(not t or len(t) > 30 for t in tags):
            raise ValueError("tags must be 1-30 characters")
        return tags


class CaseWrite(BaseModel):
    input: Any
    expected: Any
    is_sample: bool = False
    explanation: str | None = Field(default=None, max_length=2000)
    position: int | None = Field(default=None, ge=0, le=10_000)

    @model_validator(mode="after")
    def _bounded(self) -> CaseWrite:
        if _json_size(self.input) + _json_size(self.expected) > MAX_TEST_JSON_BYTES:
            raise ValueError(f"a test case must be at most {MAX_TEST_JSON_BYTES} bytes of JSON")
        return self


class Note(BaseModel):
    """A user's note on a pattern or problem; empty content and no `updated_at` when none was written."""

    content: str
    updated_at: datetime | None = None


class NoteWrite(BaseModel):
    content: str = Field(max_length=MAX_NOTE_CHARS)
