"""DSA API end to end: seeded catalog, Run/Submit through the queue, progress, isolation, admin.

The judge is a local stand-in that really executes the generated Python program in a subprocess
(no sandbox), so driver -> runner -> verdict -> progress is exercised for real.
"""

import asyncio
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from app.core.rate_limit import SlidingWindowLimiter
from app.modules.auth.models import User
from app.modules.dsa import cli as dsa_cli
from app.modules.dsa import service as dsa_service
from app.modules.dsa.content.build import PatternSource, build_pattern, render
from app.modules.dsa.content.model import Example, ProblemSource, function
from app.modules.dsa.judge.client import JudgeUnavailableError, SandboxCommand, SandboxResult
from app.modules.dsa.judge.runner import Runner
from app.modules.dsa.models import DsaProblem, DsaSubmission, DsaUserProgress
from app.modules.dsa.runtime import build_queue, install_queue
from app.modules.dsa.seeder import seed
from app.modules.dsa.worker import JudgeWorker
from sqlalchemy import select

CATALOG = {
    "patterns": [
        {"number": 1, "slug": "two-pointers", "name": "Two Pointers", "week": 1, "description": "Two indices."},
    ],
    "problems": [
        {"pattern": 1, "slug": "array-sum", "title": "Array Sum", "difficulty": "easy", "tags": [], "order": 0},
        {"pattern": 1, "slug": "coming-later", "title": "Coming Later", "difficulty": "hard", "tags": [], "order": 1},
    ],
}
SOURCE = ProblemSource(
    title="Array Sum",
    statement="Return the sum of `nums`.",
    constraints="- `0 <= nums.length <= 100`",
    signature=function("arraySum", [("nums", "int[]")], "int"),
    reference=lambda nums: sum(nums),
    examples=[Example([[1, 2, 3]], "1 + 2 + 3 = 6."), Example([[5]])],
    edge_cases=[[[]], [[-1, 1]], [[7, 7, 7, 7]]],
)
GOOD = "class Solution:\n    def arraySum(self, nums):\n        print('debug', len(nums))\n        return sum(nums)\n"
WRONG_ON_HIDDEN = "class Solution:\n    def arraySum(self, nums):\n        if not nums:\n            raise ValueError('secret ' + str(nums))\n        return sum(nums)\n"
BASE = "/api/v1/dsa"


class LocalPythonJudge:
    """Executes the sandbox command's Python program locally (tests only)."""

    async def run(self, command: SandboxCommand) -> SandboxResult:
        return await asyncio.to_thread(self._run, command)

    def _run(self, command: SandboxCommand) -> SandboxResult:
        with tempfile.TemporaryDirectory() as tmp:
            for name, content in command.copy_in.items():
                Path(tmp, name).write_text(content, encoding="utf-8")
            try:
                proc = subprocess.run([sys.executable, "main.py"], cwd=tmp, capture_output=True, text=True, timeout=30)
            except subprocess.TimeoutExpired:
                return SandboxResult("Time Limit Exceeded")
            result_path = Path(tmp, "result.jsonl")
            files = {"stdout": proc.stdout, "stderr": proc.stderr}
            if result_path.exists():
                files["result.jsonl"] = result_path.read_text(encoding="utf-8")
            status = "Accepted" if proc.returncode == 0 else "Nonzero Exit Status"
            return SandboxResult(status, exit_status=proc.returncode, memory_bytes=1 << 20, files=files)

    async def delete_file(self, file_id: str) -> None:
        return None


class DownJudge:
    async def run(self, command):
        raise JudgeUnavailableError("down")

    async def delete_file(self, file_id):
        return None


@pytest.fixture
async def dsa(client, tmp_path):
    (tmp_path / "catalog.json").write_text(json.dumps(CATALOG))
    (tmp_path / "p01-two-pointers.json").write_text(render(build_pattern(PatternSource(1, [SOURCE], "t"), CATALOG)))
    async with client.session_factory() as db:
        await seed(db, seeds_dir=tmp_path)
        await db.commit()
    dsa_service.reset_limiters()
    queues = []

    async def start(judge=None):
        queue = build_queue(JudgeWorker(client.session_factory, Runner(judge or LocalPythonJudge())), 2)
        await queue.start()
        install_queue(queue)
        queues.append(queue)
        return queue

    yield start
    for queue in queues:
        await queue.stop()
    install_queue(None)
    dsa_service.reset_limiters()


async def _user(client, name: str) -> dict[str, str]:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"username": name, "email": f"{name}@example.com", "password": "password123", "display_name": name},
    )
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


async def _wait(client, url: str, headers) -> dict:
    for _ in range(200):
        body = (await client.get(url, headers=headers)).json()
        if body["status"] in ("done", "error"):
            return body
        await asyncio.sleep(0.05)
    raise AssertionError(f"job did not finish: {body}")


async def test_catalog_views_hide_hidden_tests_and_drafts(client, dsa):
    h = await _user(client, "alice")
    patterns = (await client.get(f"{BASE}/patterns", headers=h)).json()
    assert patterns == [
        {
            "slug": "two-pointers",
            "number": 1,
            "name": "Two Pointers",
            "description": "Two indices.",
            "week": 1,
            "total": 1,
            "solved": 0,
            "attempted": 0,
        }
    ]
    detail = (await client.get(f"{BASE}/patterns/two-pointers", headers=h)).json()
    assert [(p["slug"], p["status"], p["progress"]) for p in detail["problems"]] == [
        ("array-sum", "published", "not_started"),
        ("coming-later", "draft", "not_started"),
    ]
    problem = (await client.get(f"{BASE}/problems/array-sum", headers=h)).json()
    assert len(problem["samples"]) == 2 and problem["samples"][0]["explanation"] == "1 + 2 + 3 = 6."
    assert set(problem["starter_code"]) == {"python", "javascript", "cpp", "java"}
    assert "tests" not in problem
    draft = (await client.get(f"{BASE}/problems/coming-later", headers=h)).json()
    assert draft["status"] == "draft" and draft["samples"] == [] and draft["starter_code"] == {}
    assert (await client.get(f"{BASE}/problems/nope", headers=h)).status_code == 404
    assert (await client.get(f"{BASE}/patterns")).status_code == 401


async def test_submit_accepted_updates_progress(client, dsa):
    await dsa()
    h = await _user(client, "bob")
    accepted = await client.post(
        f"{BASE}/problems/array-sum/submissions", json={"language": "python", "code": GOOD}, headers=h
    )
    assert accepted.status_code == 202 and accepted.json()["status"] == "pending"
    result = await _wait(client, f"{BASE}/submissions/{accepted.json()['id']}", h)
    assert result["verdict"] == "Accepted" and result["passed"] == result["total"] == 5
    assert result["code"] == GOOD and result["problem_slug"] == "array-sum"

    patterns = (await client.get(f"{BASE}/patterns", headers=h)).json()
    assert patterns[0]["solved"] == 1
    problem = (await client.get(f"{BASE}/problems/array-sum", headers=h)).json()
    assert problem["progress"] == "solved"
    history = (await client.get(f"{BASE}/problems/array-sum/submissions", headers=h)).json()
    assert history["total"] == 1 and "code" not in history["items"][0]


async def test_hidden_failure_reveals_only_exception_type(client, dsa):
    await dsa()
    h = await _user(client, "carol")
    sub = await client.post(
        f"{BASE}/problems/array-sum/submissions", json={"language": "python", "code": WRONG_ON_HIDDEN}, headers=h
    )
    result = await _wait(client, f"{BASE}/submissions/{sub.json()['id']}", h)
    assert result["verdict"] == "Runtime Error" and result["failed_case"] == 3
    assert result["message"] == "ValueError"  # not "ValueError: secret []"
    problem = (await client.get(f"{BASE}/problems/array-sum", headers=h)).json()
    assert problem["progress"] == "attempted"


async def test_run_samples_and_custom_inputs(client, dsa):
    await dsa()
    h = await _user(client, "dave")
    started = await client.post(
        f"{BASE}/problems/array-sum/run",
        json={"language": "python", "code": GOOD, "custom_inputs": [[[10, 20]]]},
        headers=h,
    )
    assert started.status_code == 202
    result = await _wait(client, f"{BASE}/runs/{started.json()['id']}", h)
    assert result["verdict"] == "Accepted"
    assert [(c["passed"], c["is_custom"], c["actual"]) for c in result["cases"]] == [
        (True, False, 6),
        (True, False, 5),
        (None, True, 30),
    ]
    assert result["cases"][2]["expected"] is None and "debug" in result["stdout"]
    async with client.session_factory() as db:
        assert (await db.execute(select(DsaSubmission))).first() is None  # runs are not stored


async def test_run_rejects_bad_custom_input_and_draft(client, dsa):
    await dsa()
    h = await _user(client, "erin")
    bad = await client.post(
        f"{BASE}/problems/array-sum/run", json={"language": "python", "code": GOOD, "custom_inputs": [["x"]]}, headers=h
    )
    assert bad.status_code == 400
    draft = await client.post(
        f"{BASE}/problems/coming-later/submissions", json={"language": "python", "code": GOOD}, headers=h
    )
    assert draft.status_code == 409
    lang = await client.post(
        f"{BASE}/problems/array-sum/submissions", json={"language": "cobol", "code": GOOD}, headers=h
    )
    assert lang.status_code == 422
    big = await client.post(
        f"{BASE}/problems/array-sum/submissions", json={"language": "python", "code": "x" * 70_000}, headers=h
    )
    assert big.status_code == 422


async def test_cross_user_isolation(client, dsa):
    await dsa()
    owner = await _user(client, "frank")
    other = await _user(client, "grace")
    sub = await client.post(
        f"{BASE}/problems/array-sum/submissions", json={"language": "python", "code": GOOD}, headers=owner
    )
    run = await client.post(f"{BASE}/problems/array-sum/run", json={"language": "python", "code": GOOD}, headers=owner)
    await _wait(client, f"{BASE}/submissions/{sub.json()['id']}", owner)
    await _wait(client, f"{BASE}/runs/{run.json()['id']}", owner)

    assert (await client.get(f"{BASE}/submissions/{sub.json()['id']}", headers=other)).status_code == 404
    assert (await client.get(f"{BASE}/runs/{run.json()['id']}", headers=other)).status_code == 404
    assert (await client.get(f"{BASE}/problems/array-sum/submissions", headers=other)).json() == {
        "items": [],
        "total": 0,
    }
    assert (await client.get(f"{BASE}/patterns", headers=other)).json()[0]["solved"] == 0


async def test_judge_not_configured_is_503(client, dsa):
    h = await _user(client, "heidi")
    resp = await client.post(
        f"{BASE}/problems/array-sum/submissions", json={"language": "python", "code": GOOD}, headers=h
    )
    assert resp.status_code == 503


async def test_unreachable_judge_fails_closed(client, dsa):
    await dsa(DownJudge())
    h = await _user(client, "ivan")
    sub = await client.post(
        f"{BASE}/problems/array-sum/submissions", json={"language": "python", "code": GOOD}, headers=h
    )
    result = await _wait(client, f"{BASE}/submissions/{sub.json()['id']}", h)
    assert result["status"] == "error" and result["verdict"] == "Internal Error"
    async with client.session_factory() as db:
        assert (await db.execute(select(DsaUserProgress))).first() is None


async def test_rate_limits(client, dsa, monkeypatch):
    await dsa()
    limiter_pair = (SlidingWindowLimiter(1, 60), SlidingWindowLimiter(1, 60))
    monkeypatch.setattr(dsa_service, "_limiters", lambda settings: limiter_pair)
    h = await _user(client, "judy")
    first = await client.post(
        f"{BASE}/problems/array-sum/submissions", json={"language": "python", "code": GOOD}, headers=h
    )
    second = await client.post(
        f"{BASE}/problems/array-sum/submissions", json={"language": "python", "code": GOOD}, headers=h
    )
    assert (first.status_code, second.status_code) == (202, 429)


async def test_unfinished_submissions_are_requeued_on_start(client, dsa):
    await _user(client, "mallory")
    async with client.session_factory() as db:
        user = (await db.execute(select(User).where(User.username == "mallory"))).scalar_one()
        problem = (await db.execute(select(DsaProblem).where(DsaProblem.slug == "array-sum"))).scalar_one()
        db.add(DsaSubmission(user_id=user.id, problem_id=problem.id, language="python", code=GOOD, status="running"))
        await db.commit()
    queue = await dsa()
    await queue.drain()
    async with client.session_factory() as db:
        submission = (await db.execute(select(DsaSubmission))).scalar_one()
        assert submission.status == "done" and submission.verdict == "Accepted"


async def test_admin_endpoints(client, dsa):
    user = await _user(client, "olivia")
    assert (await client.get(f"{BASE}/me", headers=user)).json() == {"can_edit": False}
    assert (await client.get(f"{BASE}/admin/problems/array-sum", headers=user)).status_code == 403
    assert (
        await client.put(f"{BASE}/admin/problems/array-sum", json={"statement": "x"}, headers=user)
    ).status_code == 403

    async with client.session_factory() as db:
        await dsa_cli.set_admin(db, "olivia", True)
        await db.commit()
    assert (await client.get(f"{BASE}/me", headers=user)).json() == {"can_edit": True}

    admin_view = (await client.get(f"{BASE}/admin/problems/array-sum", headers=user)).json()
    assert len(admin_view["tests"]) == 5 and admin_view["edited_in_ui"] is False

    updated = await client.put(f"{BASE}/admin/problems/array-sum", json={"statement": "New wording."}, headers=user)
    assert (
        updated.status_code == 200 and updated.json()["statement"] == "New wording." and updated.json()["edited_in_ui"]
    )

    bad_sig = await client.put(
        f"{BASE}/admin/problems/array-sum",
        json={
            "signature": {
                "kind": "function",
                "name": "f",
                "params": [{"name": "s", "type": "string"}],
                "returns": "int",
            }
        },
        headers=user,
    )
    assert bad_sig.status_code == 400  # existing tests no longer match

    bad_test = await client.post(
        f"{BASE}/admin/problems/array-sum/tests", json={"input": [[1]], "expected": "six"}, headers=user
    )
    assert bad_test.status_code == 400
    added = await client.post(
        f"{BASE}/admin/problems/array-sum/tests", json={"input": [[2, 2]], "expected": 4}, headers=user
    )
    assert added.status_code == 201 and added.json()["position"] == 5
    dup = await client.post(
        f"{BASE}/admin/problems/array-sum/tests", json={"input": [[1]], "expected": 1, "position": 5}, headers=user
    )
    assert dup.status_code == 409
    test_id = added.json()["id"]
    edited = await client.put(
        f"{BASE}/admin/tests/{test_id}",
        json={"input": [[3]], "expected": 3, "is_sample": True, "explanation": "one"},
        headers=user,
    )
    assert edited.status_code == 200 and edited.json()["is_sample"] is True
    assert (await client.delete(f"{BASE}/admin/tests/{test_id}", headers=user)).status_code == 204

    publish_draft = await client.put(f"{BASE}/admin/problems/coming-later", json={"status": "published"}, headers=user)
    assert publish_draft.status_code == 400  # no signature / samples yet
