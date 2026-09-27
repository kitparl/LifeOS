import json

import httpx
import pytest
from app.modules.dsa.judge import client as judge_client
from app.modules.dsa.judge.client import (
    CachedFile,
    GoJudgeClient,
    JudgeUnavailableError,
    SandboxCommand,
    SandboxResult,
)
from app.modules.dsa.judge.runner import Limits, Runner, parse_results

SPEC = {"kind": "function", "name": "f", "params": [{"name": "x", "type": "int"}], "returns": "int"}


def _patch_transport(monkeypatch, handler):
    def factory(base_url: str, token: str, timeout: float) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers={"Authorization": f"Bearer {token}"},
            transport=httpx.MockTransport(handler),
        )

    monkeypatch.setattr(judge_client, "_http_client", factory)


# ---------------------------------------------------------------- GoJudgeClient


async def test_run_sends_limits_and_token(monkeypatch):
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json=[
                {
                    "status": "Accepted",
                    "exitStatus": 0,
                    "time": 5_000_000,
                    "memory": 4096,
                    "files": {"stdout": "hi"},
                    "fileIds": {"main": "abc"},
                }
            ],
        )

    _patch_transport(monkeypatch, handler)
    cmd = SandboxCommand(
        args=["./main"],
        cpu_ms=1500,
        clock_ms=3000,
        memory_mb=64,
        proc_limit=4,
        copy_in={"a": "x", "b": CachedFile("id1")},
        copy_out=["r?"],
        copy_out_cached=["main"],
    )
    result = await GoJudgeClient("http://judge:5050/", "tok", 5).run(cmd)

    assert seen["auth"] == "Bearer tok"
    body = seen["body"]["cmd"][0]
    assert body["cpuLimit"] == 1_500_000_000 and body["clockLimit"] == 3_000_000_000
    assert body["memoryLimit"] == 64 << 20 and body["procLimit"] == 4
    assert body["copyIn"] == {"a": {"content": "x"}, "b": {"fileId": "id1"}}
    assert body["copyOut"] == ["stdout", "stderr", "r?"] and body["copyOutCached"] == ["main"]
    assert result == SandboxResult("Accepted", 0, 5_000_000, 4096, {"stdout": "hi"}, {"main": "abc"}, None)


@pytest.mark.parametrize(
    "handler",
    [
        lambda r: httpx.Response(500),
        lambda r: httpx.Response(401),
        lambda r: httpx.Response(200, content=b"not json"),
        lambda r: httpx.Response(200, json={"status": "Accepted"}),
        lambda r: httpx.Response(200, json=[{"no": "status"}]),
    ],
)
async def test_run_failures_raise_unavailable(monkeypatch, handler):
    _patch_transport(monkeypatch, handler)
    with pytest.raises(JudgeUnavailableError):
        await GoJudgeClient("http://judge", "t", 5).run(SandboxCommand(["x"], 1, 1, 1, 1))


async def test_run_unreachable(monkeypatch):
    def handler(request):
        raise httpx.ConnectError("refused")

    _patch_transport(monkeypatch, handler)
    with pytest.raises(JudgeUnavailableError):
        await GoJudgeClient("http://judge", "t", 5).run(SandboxCommand(["x"], 1, 1, 1, 1))


async def test_delete_file_never_raises(monkeypatch):
    calls = []

    def handler(request):
        calls.append((request.method, request.url.path))
        raise httpx.ConnectError("down")

    _patch_transport(monkeypatch, handler)
    await GoJudgeClient("http://judge", "t", 5).delete_file("abc")
    assert calls == [("DELETE", "/file/abc")]


# ---------------------------------------------------------------- Runner


class ScriptedClient:
    def __init__(self, *results: SandboxResult):
        self.results = list(results)
        self.commands: list[SandboxCommand] = []
        self.deleted: list[str] = []

    async def run(self, command: SandboxCommand) -> SandboxResult:
        self.commands.append(command)
        return self.results.pop(0)

    async def delete_file(self, file_id: str) -> None:
        self.deleted.append(file_id)


def _lines(*rows) -> str:
    return "".join(json.dumps(r) + "\n" for r in rows)


async def test_interpreted_run_single_call():
    fake = ScriptedClient(
        SandboxResult(
            "Accepted",
            memory_bytes=8192,
            files={"result.jsonl": _lines({"i": 0, "ok": True, "out": 2, "ms": 1.5}), "stdout": "dbg"},
        )
    )
    compiled, run = await Runner(fake).run("python", SPEC, "code", [[1]], Limits(1000, 256))
    assert compiled is None
    assert run.status == "Accepted" and run.memory_kb == 8 and run.stdout == "dbg"
    assert run.cases[0].out == 2
    (cmd,) = fake.commands
    assert set(cmd.copy_in) == {"main.py", "tests.json"}
    assert json.loads(cmd.copy_in["tests.json"]) == [[1]]
    assert cmd.cpu_ms == 1000 * 3 + 500 and cmd.memory_mb == 256 + 64
    assert cmd.copy_out == ["result.jsonl?"]


async def test_compiled_run_uses_cached_artifact_and_releases_it():
    fake = ScriptedClient(
        SandboxResult("Accepted", file_ids={"main": "bin1"}),
        SandboxResult("Accepted", files={"result.jsonl": _lines({"i": 0, "ok": True, "out": 1, "ms": 0.1})}),
    )
    compiled, run = await Runner(fake).run("cpp", SPEC, "code", [[1]], Limits(1000, 256))
    assert compiled is not None and compiled.ok and run.cases[0].out == 1
    assert fake.commands[0].copy_out_cached == ["main"]
    assert fake.commands[1].copy_in["main"] == CachedFile("bin1")
    assert "main.cpp" not in fake.commands[1].copy_in
    assert fake.deleted == ["bin1"]


async def test_compile_error_returns_output_and_skips_run():
    fake = ScriptedClient(SandboxResult("Nonzero Exit Status", exit_status=1, files={"stderr": "error: expected ';'"}))
    compiled, run = await Runner(fake).run("java", SPEC, "code", [[1]], Limits(1000, 256))
    assert compiled is not None and not compiled.ok and "expected ';'" in compiled.output
    assert run is None and len(fake.commands) == 1


async def test_artifact_released_when_run_fails():
    class Failing(ScriptedClient):
        async def run(self, command):
            if self.commands:
                raise JudgeUnavailableError("down")
            return await super().run(command)

    fake = Failing(SandboxResult("Accepted", file_ids={"main": "bin9"}))
    with pytest.raises(JudgeUnavailableError):
        await Runner(fake).run("cpp", SPEC, "code", [[1]], Limits(1000, 256))
    assert fake.deleted == ["bin9"]


async def test_total_cpu_is_capped():
    fake = ScriptedClient(SandboxResult("Accepted"))
    await Runner(fake).run("python", SPEC, "code", [[1]] * 40, Limits(2000, 256))
    assert fake.commands[0].cpu_ms == 10_000 + 500


def test_parse_results_stops_at_malformed_or_out_of_order_line():
    text = _lines({"i": 0, "ok": True, "out": 1, "ms": 2}, {"i": 1, "ok": False, "err": "E"}) + '{"i": 2, "ok": tr'
    cases = parse_results(text)
    assert [(c.index, c.ok) for c in cases] == [(0, True), (1, False)]
    assert parse_results(_lines({"i": 1, "ok": True})) == []
    assert parse_results(_lines({"i": 0, "ok": True, "ms": "x"}))[0].ms == 0.0
