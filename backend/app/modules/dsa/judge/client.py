"""go-judge REST client (https://github.com/criyle/go-judge). The only code that knows its API.

go-judge is the sandbox Hydro's own judge daemon uses. It runs inside `infra/docker-compose.yml`
on 127.0.0.1 with a bearer token; each command gets its own namespaces (no network) and cgroup
limits. Every transport or protocol failure raises JudgeUnavailableError (callers fail closed).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)

SANDBOX_ENV = ["PATH=/usr/local/bin:/usr/bin:/bin", "HOME=/tmp", "LANG=C.UTF-8"]
STDIO_COLLECT_BYTES = 1 << 20
COPY_OUT_MAX_BYTES = 16 << 20


class JudgeUnavailableError(Exception):
    """The judge could not be reached or answered with something unusable."""


@dataclass(frozen=True)
class CachedFile:
    """A file previously stored in go-judge (copyOutCached), referenced by id."""

    file_id: str


@dataclass(frozen=True)
class SandboxCommand:
    args: list[str]
    cpu_ms: int
    clock_ms: int
    memory_mb: int
    proc_limit: int
    copy_in: dict[str, str | CachedFile] = field(default_factory=dict)
    copy_out: list[str] = field(default_factory=list)
    copy_out_cached: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SandboxResult:
    status: str
    exit_status: int = 0
    time_ns: int = 0
    memory_bytes: int = 0
    files: dict[str, str] = field(default_factory=dict)
    file_ids: dict[str, str] = field(default_factory=dict)
    error: str | None = None


class JudgeClient(Protocol):
    async def run(self, command: SandboxCommand) -> SandboxResult: ...

    async def delete_file(self, file_id: str) -> None: ...


def _http_client(base_url: str, token: str, timeout: float) -> httpx.AsyncClient:
    """Single construction point for go-judge HTTP clients (tests patch this seam)."""
    return httpx.AsyncClient(base_url=base_url, timeout=timeout, headers={"Authorization": f"Bearer {token}"})


def _payload(command: SandboxCommand) -> dict:
    mem = command.memory_mb << 20
    copy_in = {
        name: {"fileId": src.file_id} if isinstance(src, CachedFile) else {"content": src}
        for name, src in command.copy_in.items()
    }
    return {
        "args": command.args,
        "env": SANDBOX_ENV,
        "files": [
            {"content": ""},
            {"name": "stdout", "max": STDIO_COLLECT_BYTES},
            {"name": "stderr", "max": STDIO_COLLECT_BYTES},
        ],
        "cpuLimit": command.cpu_ms * 1_000_000,
        "clockLimit": command.clock_ms * 1_000_000,
        "memoryLimit": mem,
        "stackLimit": mem,
        "procLimit": command.proc_limit,
        "copyIn": copy_in,
        "copyOut": ["stdout", "stderr", *command.copy_out],
        "copyOutCached": command.copy_out_cached,
        "copyOutMax": COPY_OUT_MAX_BYTES,
    }


def _parse_result(data: object) -> SandboxResult:
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise JudgeUnavailableError("unexpected /run response shape")
    r = data[0]
    status = r.get("status")
    if not isinstance(status, str):
        raise JudgeUnavailableError("missing status in /run response")
    files = r.get("files") or {}
    file_ids = r.get("fileIds") or {}
    return SandboxResult(
        status=status,
        exit_status=int(r.get("exitStatus") or 0),
        time_ns=int(r.get("time") or 0),
        memory_bytes=int(r.get("memory") or 0),
        files={str(k): str(v) for k, v in files.items()} if isinstance(files, dict) else {},
        file_ids={str(k): str(v) for k, v in file_ids.items()} if isinstance(file_ids, dict) else {},
        error=r.get("error") if isinstance(r.get("error"), str) else None,
    )


class GoJudgeClient:
    def __init__(self, base_url: str, token: str, timeout_seconds: float):
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout_seconds

    async def run(self, command: SandboxCommand) -> SandboxResult:
        try:
            async with _http_client(self._base_url, self._token, self._timeout) as http:
                response = await http.post("/run", json={"cmd": [_payload(command)]})
                response.raise_for_status()
                return _parse_result(response.json())
        except JudgeUnavailableError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("go-judge /run failed: %s", type(exc).__name__)
            raise JudgeUnavailableError(type(exc).__name__) from exc

    async def delete_file(self, file_id: str) -> None:
        try:
            async with _http_client(self._base_url, self._token, self._timeout) as http:
                response = await http.delete(f"/file/{file_id}")
                if response.status_code not in (200, 204, 404):
                    response.raise_for_status()
        except httpx.HTTPError as exc:
            # A leaked cached file expires via go-judge's -file-timeout; never fail the job over it.
            logger.warning("go-judge DELETE /file failed: %s", type(exc).__name__)
