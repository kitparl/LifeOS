"""Compile once, run once over all tests, parse `result.jsonl`. No comparison here (see verdict.py)."""

from __future__ import annotations

import json
from dataclasses import dataclass

from app.modules.dsa.judge import drivers
from app.modules.dsa.judge.client import CachedFile, JudgeClient, SandboxCommand, SandboxResult
from app.modules.dsa.judge.languages import LANGUAGES, LanguageSpec
from app.modules.dsa.judge.verdict import CaseResult, CompileOutcome, RunOutcome

MAX_TOTAL_CPU_MS = 10_000
COMPILE_CPU_MS = 10_000
COMPILE_MEMORY_MB = 1024
COMPILE_PROC_LIMIT = 64
DISPLAY_OUTPUT_BYTES = 8 * 1024
RESULT_FILE = "result.jsonl"


@dataclass(frozen=True)
class Limits:
    time_limit_ms: int
    memory_limit_mb: int


def per_test_limit_ms(language: str, limits: Limits) -> float:
    return limits.time_limit_ms * LANGUAGES[language].time_factor


def truncate(text: str, limit: int = DISPLAY_OUTPUT_BYTES) -> str:
    return text if len(text) <= limit else text[:limit] + "\n… (truncated)"


class Runner:
    def __init__(self, client: JudgeClient):
        self._client = client

    async def run(
        self, language: str, spec: dict, code: str, inputs: list[object], limits: Limits
    ) -> tuple[CompileOutcome | None, RunOutcome | None]:
        """Returns (compile outcome or None if interpreted, run outcome or None if compile failed)."""
        lang = LANGUAGES[language]
        files = drivers.program(language, spec, code)
        compile_outcome: CompileOutcome | None = None
        copy_in: dict[str, str | CachedFile] = dict(files)
        artifact_id: str | None = None
        try:
            if lang.compile_args is not None:
                compile_outcome, artifact_id = await self._compile(lang, files)
                if not compile_outcome.ok:
                    return compile_outcome, None
                assert lang.artifact is not None and artifact_id is not None
                copy_in = {lang.artifact: CachedFile(artifact_id)}
            copy_in["tests.json"] = json.dumps(inputs, separators=(",", ":"))
            result = await self._client.run(self._run_command(lang, limits, len(inputs), copy_in))
            return compile_outcome, _run_outcome(result)
        finally:
            if artifact_id is not None:
                await self._client.delete_file(artifact_id)

    async def _compile(self, lang: LanguageSpec, files: dict[str, str]) -> tuple[CompileOutcome, str | None]:
        assert lang.compile_args is not None and lang.artifact is not None
        result = await self._client.run(
            SandboxCommand(
                args=list(lang.compile_args),
                cpu_ms=COMPILE_CPU_MS,
                clock_ms=COMPILE_CPU_MS * 2,
                memory_mb=COMPILE_MEMORY_MB,
                proc_limit=COMPILE_PROC_LIMIT,
                copy_in=dict(files),
                copy_out_cached=[lang.artifact],
            )
        )
        artifact_id = result.file_ids.get(lang.artifact)
        if result.status != "Accepted" or artifact_id is None:
            output = result.files.get("stderr") or result.files.get("stdout") or result.status
            if artifact_id is not None:
                await self._client.delete_file(artifact_id)
            return CompileOutcome(False, truncate(output)), None
        return CompileOutcome(True), artifact_id

    @staticmethod
    def _run_command(
        lang: LanguageSpec, limits: Limits, test_count: int, copy_in: dict[str, str | CachedFile]
    ) -> SandboxCommand:
        per_test = limits.time_limit_ms * lang.time_factor
        cpu_ms = int(min(per_test * max(test_count, 1), MAX_TOTAL_CPU_MS) + lang.startup_ms)
        return SandboxCommand(
            args=lang.run_args(limits.memory_limit_mb),
            cpu_ms=cpu_ms,
            clock_ms=cpu_ms * 2,
            memory_mb=limits.memory_limit_mb + lang.memory_overhead_mb,
            proc_limit=lang.proc_limit,
            copy_in=copy_in,
            copy_out=[f"{RESULT_FILE}?"],
        )


def _run_outcome(result: SandboxResult) -> RunOutcome:
    return RunOutcome(
        status=result.status,
        time_ms=result.time_ns // 1_000_000,
        memory_kb=result.memory_bytes // 1024,
        cases=parse_results(result.files.get(RESULT_FILE, "")),
        stdout=truncate(result.files.get("stdout", "")),
        stderr=truncate(result.files.get("stderr", "")),
    )


def parse_results(text: str) -> list[CaseResult]:
    """Parse driver lines in order; stop at the first malformed line (the program died mid-write)."""
    cases: list[CaseResult] = []
    for expected_index, line in enumerate(text.splitlines()):
        try:
            row = json.loads(line)
        except ValueError:
            break
        if not isinstance(row, dict) or row.get("i") != expected_index or not isinstance(row.get("ok"), bool):
            break
        if row["ok"]:
            ms = row.get("ms")
            ms = float(ms) if isinstance(ms, (int, float)) and not isinstance(ms, bool) else 0.0
            cases.append(CaseResult(expected_index, ok=True, out=row.get("out"), ms=max(ms, 0.0)))
        else:
            err = row.get("err")
            cases.append(CaseResult(expected_index, ok=False, err=str(err)[:500] if err is not None else "error"))
    return cases
