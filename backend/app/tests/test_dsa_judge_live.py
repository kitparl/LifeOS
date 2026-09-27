"""Live go-judge check for all four languages (skipped unless DSA_JUDGE_URL / DSA_JUDGE_TOKEN are set).

cd infra && DSA_JUDGE_TOKEN=dev docker compose --profile judge up -d --build judge
cd backend && DSA_JUDGE_URL=http://127.0.0.1:5050 DSA_JUDGE_TOKEN=dev pytest app/tests/test_dsa_judge_live.py
"""

import os

import pytest
from app.modules.dsa.judge import client as judge_client
from app.modules.dsa.judge.client import GoJudgeClient
from app.modules.dsa.judge.runner import Limits, Runner, per_test_limit_ms
from app.modules.dsa.judge.verdict import Grading, Verdict, decide
from app.tests.test_dsa_drivers import CASES, SOLUTIONS, TWO_SUM

LIVE_URL = os.environ.get("DSA_JUDGE_URL", "")
LIVE_TOKEN = os.environ.get("DSA_JUDGE_TOKEN", "")
REAL_HTTP_CLIENT = judge_client._http_client  # captured before the offline autouse patch applies

pytestmark = pytest.mark.skipif(not LIVE_URL, reason="DSA_JUDGE_URL not set (live go-judge test)")
LANGUAGES = ["python", "javascript", "cpp", "java"]


@pytest.fixture
def live_runner(monkeypatch):
    monkeypatch.setattr(judge_client, "_http_client", REAL_HTTP_CLIENT)
    return Runner(GoJudgeClient(LIVE_URL, LIVE_TOKEN, 60))


async def _judge(
    runner: Runner, language: str, spec: dict, code: str, inputs: list, expected: list, limits=Limits(2000, 256)
):
    grading = Grading(inputs, expected, per_test_limit_ms(language, limits), "exact")
    compiled, run = await runner.run(language, spec, code, inputs, limits)
    return decide(compiled, run, grading)


@pytest.mark.parametrize("language", LANGUAGES)
@pytest.mark.parametrize(("spec", "tests", "expected"), CASES, ids=[c[0]["name"] for c in CASES])
async def test_accepted_in_sandbox(live_runner, language, spec, tests, expected):
    outcome = await _judge(live_runner, language, spec, SOLUTIONS[spec["name"]][language], tests, expected)
    assert outcome.verdict == Verdict.ACCEPTED, outcome


@pytest.mark.parametrize(
    ("language", "code", "verdict"),
    [
        (
            "cpp",
            "class Solution { public: vector<int> twoSum(vector<int>& n, int t) { return {0, 1} } };",
            Verdict.COMPILE_ERROR,
        ),
        ("java", "class Solution { public int[] twoSum(int[] n, int t) { return null }", Verdict.COMPILE_ERROR),
        ("python", "class Solution:\n    def twoSum(self, n, t):\n        while True: pass\n", Verdict.TIME_LIMIT),
        (
            "cpp",
            "class Solution { public: vector<int> twoSum(vector<int>& n, int t) { vector<int> v; while (true) v.push_back(1); } };",
            Verdict.MEMORY_LIMIT,
        ),
        ("javascript", "var twoSum = function(n, t) { return [1, 0]; };", Verdict.WRONG_ANSWER),
        (
            "cpp",
            "class Solution { public: vector<int> twoSum(vector<int>& n, int t) { int* p = nullptr; return {*p}; } };",
            Verdict.RUNTIME_ERROR,
        ),
    ],
)
async def test_failure_verdicts_in_sandbox(live_runner, language, code, verdict):
    outcome = await _judge(live_runner, language, TWO_SUM, code, [[[2, 7], 9]], [[0, 1]], Limits(1000, 64))
    assert outcome.verdict == verdict, outcome


async def test_no_network_in_sandbox(live_runner):
    code = (
        "import socket\n"
        "class Solution:\n"
        "    def twoSum(self, n, t):\n"
        "        socket.create_connection(('1.1.1.1', 53), timeout=2)\n"
        "        return [0, 1]\n"
    )
    outcome = await _judge(live_runner, "python", TWO_SUM, code, [[[2, 7], 9]], [[0, 1]])
    assert outcome.verdict == Verdict.RUNTIME_ERROR, outcome
