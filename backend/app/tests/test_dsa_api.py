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
from app.modules.dsa.content.sources.p01_two_pointers_b import SUM_OF_SQUARES
from app.modules.dsa.judge.client import JudgeUnavailableError, SandboxCommand, SandboxResult
from app.modules.dsa.judge.runner import Runner
from app.modules.dsa.judge.verdict import CaseResult, RunOutcome
from app.modules.dsa.models import DsaProblem, DsaSubmission, DsaUserProgress
from app.modules.dsa.runtime import build_queue, install_queue
from app.modules.dsa.seeder import seed
from app.modules.dsa.worker import NO_REFERENCE, REFERENCE_FAILED, JudgeWorker
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


SQUARES_CATALOG = {
    "patterns": [
        *CATALOG["patterns"],
        {"number": 2, "slug": "extra", "name": "Extra", "week": 1, "description": "Real sources."},
    ],
    "problems": [
        *CATALOG["problems"],
        {
            "pattern": 2,
            "slug": "sum-of-square-numbers",
            "title": "Sum of Square Numbers",
            "difficulty": "medium",
            "tags": [],
            "order": 0,
        },
    ],
}
SQUARES = (
    "import math\nclass Solution:\n    def judgeSquareSum(self, c):\n"
    "        return any(math.isqrt(c - a * a) ** 2 == c - a * a for a in range(math.isqrt(c) + 1))\n"
)
ALWAYS_FALSE = "class Solution:\n    def judgeSquareSum(self, c):\n        return False\n"


@pytest.fixture
async def squares(client, dsa, tmp_path):
    """Adds the real "Sum of Square Numbers" (it has a reference solution) as pattern 2."""
    seeds = tmp_path / "squares"
    seeds.mkdir()
    (seeds / "catalog.json").write_text(json.dumps(SQUARES_CATALOG))
    (seeds / "p01-two-pointers.json").write_text(
        render(build_pattern(PatternSource(1, [SOURCE], "t"), SQUARES_CATALOG))
    )
    (seeds / "p02-extra.json").write_text(
        render(build_pattern(PatternSource(2, [SUM_OF_SQUARES], "t"), SQUARES_CATALOG))
    )
    async with client.session_factory() as db:
        await seed(db, seeds_dir=seeds)
        await db.commit()
    return dsa


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


async def test_parallel_first_submissions_all_finish_and_count(client, dsa):
    await dsa()  # 2 workers
    h = await _user(client, "pat")
    ids = []
    for _ in range(3):
        resp = await client.post(
            f"{BASE}/problems/array-sum/submissions", json={"language": "python", "code": GOOD}, headers=h
        )
        ids.append(resp.json()["id"])
    results = [await _wait(client, f"{BASE}/submissions/{i}", h) for i in ids]
    assert [r["verdict"] for r in results] == ["Accepted"] * 3
    async with client.session_factory() as db:
        progress = (await db.execute(select(DsaUserProgress))).scalar_one()
    assert progress.attempt_count == 3 and progress.status == "solved"


async def test_submit_shows_first_failing_test(client, dsa):
    await dsa()
    h = await _user(client, "carol")
    sub = await client.post(
        f"{BASE}/problems/array-sum/submissions", json={"language": "python", "code": WRONG_ON_HIDDEN}, headers=h
    )
    result = await _wait(client, f"{BASE}/submissions/{sub.json()['id']}", h)
    assert result["verdict"] == "Runtime Error" and result["failed_case"] == 3
    assert result["message"].startswith("ValueError: secret []")
    failed = result["failed_test"]
    assert (failed["input"], failed["expected"], failed["is_sample"], failed["answered"]) == ([[]], 0, False, True)
    assert failed["error"].startswith("ValueError: secret []")
    problem = (await client.get(f"{BASE}/problems/array-sum", headers=h)).json()
    assert problem["progress"] == "attempted"


async def test_accepted_submission_has_no_failed_test(client, dsa):
    await dsa()
    h = await _user(client, "carl")
    sub = await client.post(f"{BASE}/problems/array-sum/submissions", json={"language": "python", "code": GOOD}, headers=h)
    result = await _wait(client, f"{BASE}/submissions/{sub.json()['id']}", h)
    assert result["verdict"] == "Accepted" and result["failed_case"] is None and result["failed_test"] is None


async def test_wrong_answer_records_actual_output(client, dsa):
    await dsa()
    h = await _user(client, "cleo")
    off_by_one = "class Solution:\n    def arraySum(self, nums):\n        return sum(nums) + (len(nums) == 2)\n"
    sub = await client.post(
        f"{BASE}/problems/array-sum/submissions", json={"language": "python", "code": off_by_one}, headers=h
    )
    result = await _wait(client, f"{BASE}/submissions/{sub.json()['id']}", h)
    assert result["verdict"] == "Wrong Answer" and result["failed_case"] == 4
    assert result["failed_test"] == {
        "input": [[-1, 1]],
        "expected": 0,
        "actual": 1,
        "error": None,
        "answered": True,
        "is_sample": False,
    }


async def test_run_checks_example_cases_and_runs_custom_ones(client, dsa):
    await dsa()
    h = await _user(client, "dave")
    started = await client.post(
        f"{BASE}/problems/array-sum/run",
        json={"language": "python", "code": GOOD, "inputs": [[[5]], [[10, 20]]]},
        headers=h,
    )
    assert started.status_code == 202
    result = await _wait(client, f"{BASE}/runs/{started.json()['id']}", h)
    assert result["verdict"] == "Accepted"
    # Only the cases sent run, in order; the one equal to an example is compared with its output.
    assert [(c["input"], c["expected"], c["passed"], c["is_custom"], c["actual"]) for c in result["cases"]] == [
        ([[5]], 5, True, False, 5),
        ([[10, 20]], None, None, True, 30),
    ]
    assert "debug" in result["stdout"]
    async with client.session_factory() as db:
        assert (await db.execute(select(DsaSubmission))).first() is None  # runs are not stored


async def test_run_wrong_answer_on_example_case(client, dsa):
    await dsa()
    h = await _user(client, "dina")
    wrong = "class Solution:\n    def arraySum(self, nums):\n        return 0\n"
    started = await client.post(
        f"{BASE}/problems/array-sum/run", json={"language": "python", "code": wrong, "inputs": [[[1, 2, 3]]]}, headers=h
    )
    result = await _wait(client, f"{BASE}/runs/{started.json()['id']}", h)
    assert result["verdict"] == "Wrong Answer"
    assert [(c["expected"], c["actual"], c["passed"]) for c in result["cases"]] == [(6, 0, False)]


async def _run(client, slug: str, code: str, inputs: list, headers) -> dict:
    started = await client.post(
        f"{BASE}/problems/{slug}/run", json={"language": "python", "code": code, "inputs": inputs}, headers=headers
    )
    assert started.status_code == 202, started.text
    return await _wait(client, f"{BASE}/runs/{started.json()['id']}", headers)


async def test_run_checks_custom_cases_against_the_reference(client, squares):
    await squares()
    result = await _run(client, "sum-of-square-numbers", SQUARES, [[5], [2]], await _user(client, "rhea"))
    assert result["verdict"] == "Accepted"
    assert [(c["expected"], c["passed"], c["is_custom"], c["unchecked_reason"]) for c in result["cases"]] == [
        (True, True, False, None),
        (True, True, True, None),
    ]


async def test_custom_case_failing_the_reference_is_wrong_answer(client, squares):
    await squares()
    result = await _run(client, "sum-of-square-numbers", ALWAYS_FALSE, [[2]], await _user(client, "remy"))
    assert result["verdict"] == "Wrong Answer"
    assert (result["cases"][0]["expected"], result["cases"][0]["passed"]) == (True, False)


async def test_custom_case_the_reference_cannot_handle_stays_unchecked(client, squares):
    await squares()
    # math.isqrt(-5) raises inside the reference: the input is outside the constraints.
    result = await _run(client, "sum-of-square-numbers", ALWAYS_FALSE, [[-5]], await _user(client, "rosa"))
    assert result["verdict"] == "Accepted"
    case = result["cases"][0]
    assert (case["expected"], case["passed"], case["actual"], case["unchecked_reason"]) == (
        None,
        None,
        False,
        REFERENCE_FAILED,
    )


async def test_custom_cases_without_reference_say_why(client, dsa):
    await dsa()
    result = await _run(client, "array-sum", GOOD, [[[10, 20]]], await _user(client, "ruth"))
    assert result["cases"][0]["unchecked_reason"] == NO_REFERENCE


async def test_reference_failure_never_fails_the_run(client, squares, monkeypatch):
    async def broken(self, files, inputs, limits):
        raise RuntimeError("reference run blew up")

    monkeypatch.setattr(Runner, "run_reference", broken)
    await squares()
    result = await _run(client, "sum-of-square-numbers", SQUARES, [[5], [2]], await _user(client, "rory"))
    assert result["status"] == "done" and result["verdict"] == "Accepted"
    assert result["cases"][1]["unchecked_reason"] == REFERENCE_FAILED


async def test_reference_output_outside_the_return_type_stays_unchecked(client, squares, monkeypatch):
    # e.g. Climbing Stairs with n = 90: the reference returns a number no int can hold.
    async def out_of_type(self, files, inputs, limits):
        return RunOutcome("Accepted", cases=[CaseResult(0, ok=True, out=4660046610375530309)])

    monkeypatch.setattr(Runner, "run_reference", out_of_type)
    await squares()
    result = await _run(client, "sum-of-square-numbers", SQUARES, [[2]], await _user(client, "rene"))
    assert result["verdict"] == "Accepted"
    case = result["cases"][0]
    assert (case["expected"], case["passed"], case["unchecked_reason"]) == (None, None, REFERENCE_FAILED)


async def test_example_only_run_skips_the_reference(client, squares, monkeypatch):
    calls = []

    async def counting(self, files, inputs, limits):
        calls.append(inputs)
        raise AssertionError("no reference run expected")

    monkeypatch.setattr(Runner, "run_reference", counting, raising=False)
    await squares()
    result = await _run(client, "sum-of-square-numbers", SQUARES, [[5], [3]], await _user(client, "rubi"))
    assert calls == [] and result["verdict"] == "Accepted"


async def test_run_reports_the_case_the_program_stopped_on(client, dsa):
    await dsa()
    h = await _user(client, "dora")
    crash_on_custom = (
        "import os\nclass Solution:\n    def arraySum(self, nums):\n"
        "        if nums == [9]:\n            os._exit(3)\n        return sum(nums)\n"
    )
    started = await client.post(
        f"{BASE}/problems/array-sum/run",
        json={"language": "python", "code": crash_on_custom, "inputs": [[[5]], [[9]], [[1]]]},
        headers=h,
    )
    result = await _wait(client, f"{BASE}/runs/{started.json()['id']}", h)
    # The custom case killed the process: it has no result line, but the run still says which case it was.
    assert result["verdict"] == "Runtime Error" and result["failed_case"] == 2
    assert [c["index"] for c in result["cases"]] == [0]


async def test_run_rejects_bad_cases_and_draft(client, dsa):
    await dsa()
    h = await _user(client, "erin")
    bad = await client.post(
        f"{BASE}/problems/array-sum/run", json={"language": "python", "code": GOOD, "inputs": [[[1]], ["x"]]}, headers=h
    )
    assert bad.status_code == 400 and bad.json()["detail"].startswith("Case 2:")
    for inputs in ([], [[[1]]] * 7):
        resp = await client.post(
            f"{BASE}/problems/array-sum/run", json={"language": "python", "code": GOOD, "inputs": inputs}, headers=h
        )
        assert resp.status_code == 422
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
    run = await client.post(
        f"{BASE}/problems/array-sum/run", json={"language": "python", "code": GOOD, "inputs": [[[1]]]}, headers=owner
    )
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


async def test_admin_keeps_a_sample_on_published_problems(client, dsa):
    user = await _user(client, "pia")
    async with client.session_factory() as db:
        await dsa_cli.set_admin(db, "pia", True)
        await db.commit()
    tests = (await client.get(f"{BASE}/admin/problems/array-sum", headers=user)).json()["tests"]
    first, second = [t for t in tests if t["is_sample"]]
    hidden = next(t for t in tests if not t["is_sample"])

    assert (await client.delete(f"{BASE}/admin/tests/{first['id']}", headers=user)).status_code == 204
    last_delete = await client.delete(f"{BASE}/admin/tests/{second['id']}", headers=user)
    assert last_delete.status_code == 400 and "sample" in last_delete.json()["detail"]
    unsample = await client.put(
        f"{BASE}/admin/tests/{second['id']}",
        json={"input": second["input"], "expected": second["expected"], "is_sample": False},
        headers=user,
    )
    assert unsample.status_code == 400

    moved = await client.put(
        f"{BASE}/admin/tests/{hidden['id']}",
        json={"input": hidden["input"], "expected": hidden["expected"], "position": second["position"]},
        headers=user,
    )
    assert moved.status_code == 409  # position taken: a clean conflict, not a 500


async def test_notes_per_pattern_and_problem(client, dsa):
    alice = await _user(client, "nora")
    bob = await _user(client, "otto")
    empty = {"content": "", "updated_at": None}
    for url in (f"{BASE}/patterns/two-pointers/note", f"{BASE}/problems/array-sum/note"):
        assert (await client.get(url, headers=alice)).json() == empty

    saved = await client.put(f"{BASE}/problems/array-sum/note", json={"content": "# Idea\nprefix sums"}, headers=alice)
    assert saved.status_code == 200 and saved.json()["content"] == "# Idea\nprefix sums"
    assert saved.json()["updated_at"] is not None
    await client.put(f"{BASE}/patterns/two-pointers/note", json={"content": "move the smaller side"}, headers=alice)

    # pattern and problem notes are separate, and private to their author
    assert (await client.get(f"{BASE}/patterns/two-pointers/note", headers=alice)).json()["content"] == "move the smaller side"
    assert (await client.get(f"{BASE}/problems/array-sum/note", headers=alice)).json()["content"] == "# Idea\nprefix sums"
    assert (await client.get(f"{BASE}/problems/array-sum/note", headers=bob)).json() == empty

    # updating replaces; saving blank clears
    await client.put(f"{BASE}/problems/array-sum/note", json={"content": "v2"}, headers=alice)
    assert (await client.get(f"{BASE}/problems/array-sum/note", headers=alice)).json()["content"] == "v2"
    cleared = await client.put(f"{BASE}/problems/array-sum/note", json={"content": "  \n"}, headers=alice)
    assert cleared.json() == empty
    assert (await client.get(f"{BASE}/problems/array-sum/note", headers=alice)).json() == empty

    # notes work on drafts too; unknown targets, oversized bodies and anonymous calls are rejected
    assert (await client.put(f"{BASE}/problems/coming-later/note", json={"content": "later"}, headers=alice)).status_code == 200
    assert (await client.get(f"{BASE}/problems/nope/note", headers=alice)).status_code == 404
    assert (await client.put(f"{BASE}/patterns/nope/note", json={"content": "x"}, headers=alice)).status_code == 404
    too_big = {"content": "x" * 100_001}
    assert (await client.put(f"{BASE}/problems/array-sum/note", json=too_big, headers=alice)).status_code == 422
    assert (await client.get(f"{BASE}/patterns/two-pointers/note")).status_code == 401
