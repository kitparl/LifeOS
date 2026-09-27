"""Every published problem through the real drivers (slow; opt-in with DSA_CONTENT_E2E=1).

1. Python: the problem's reference solution is submitted as the user's code; every test must pass
   through driver -> result.jsonl -> verdict, exactly as in the sandbox (run locally, no isolation).
2. C++ / JavaScript: the generated starter code must compile / load for every distinct signature.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from app.modules.dsa.content.build import discover_sources
from app.modules.dsa.judge import drivers
from app.modules.dsa.judge.runner import parse_results
from app.modules.dsa.judge.verdict import Grading, RunOutcome, Verdict, decide

pytestmark = pytest.mark.skipif(os.environ.get("DSA_CONTENT_E2E") != "1", reason="set DSA_CONTENT_E2E=1")

BACKEND = Path(__file__).resolve().parents[2]
SEEDS = BACKEND / "app" / "modules" / "dsa" / "seeds"


def _published() -> list[tuple[str, dict, object]]:
    """(slug, seed payload, reference callable) for every built problem."""
    by_title = {}
    for pattern in discover_sources():
        for source in pattern.problems:
            by_title[source.title] = source
    out = []
    for path in sorted(SEEDS.glob("p[0-9][0-9]-*.json")):
        for problem in json.loads(path.read_text(encoding="utf-8"))["problems"]:
            out.append((problem["slug"], problem, by_title[problem["title"]].reference))
    return out


PROBLEMS = _published() if os.environ.get("DSA_CONTENT_E2E") == "1" else []


def _python_user_code(spec: dict, reference) -> str:
    module, name = reference.__module__, reference.__qualname__
    header = f"import sys\nsys.path.insert(0, {str(BACKEND)!r})\nfrom {module} import {name} as _REF\n"
    if spec["kind"] == "class":
        return header + f"{spec['name']} = _REF\n"
    return header + f"class Solution:\n    def {spec['name']}(self, *args):\n        return _REF(*args)\n"


@pytest.mark.parametrize(("slug", "problem", "reference"), PROBLEMS, ids=[p[0] for p in PROBLEMS])
def test_reference_accepted_through_python_driver(slug, problem, reference, tmp_path):
    spec = problem["signature"]
    files = drivers.program("python", spec, _python_user_code(spec, reference))
    for name, content in files.items():
        (tmp_path / name).write_text(content, encoding="utf-8")
    inputs = [t["input"] for t in problem["tests"]]
    (tmp_path / "tests.json").write_text(json.dumps(inputs), encoding="utf-8")
    proc = subprocess.run([sys.executable, "main.py"], cwd=tmp_path, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr[-2000:]
    run = RunOutcome("Accepted", cases=parse_results((tmp_path / "result.jsonl").read_text(encoding="utf-8")))
    grading = Grading(
        inputs, [t["expected"] for t in problem["tests"]], 10**9, problem["compare_mode"], problem["checker"]
    )
    outcome = decide(None, run, grading)
    assert outcome.verdict == Verdict.ACCEPTED, (outcome.failed_case, outcome.message)


def _distinct_signatures() -> list[dict]:
    seen, out = set(), []
    for _, problem, _ in PROBLEMS:
        key = json.dumps(problem["signature"], sort_keys=True)
        if key not in seen:
            seen.add(key)
            out.append(problem["signature"])
    return out


SIGNATURES = _distinct_signatures()


@pytest.mark.skipif(not shutil.which("g++"), reason="g++ not installed")
@pytest.mark.parametrize("spec", SIGNATURES, ids=[s["name"] for s in SIGNATURES])
def test_cpp_starter_compiles(spec, tmp_path):
    source = drivers.program("cpp", spec, drivers.starter("cpp", spec))["main.cpp"]
    (tmp_path / "main.cpp").write_text(source, encoding="utf-8")
    proc = subprocess.run(
        ["g++", "-std=c++17", "-fsyntax-only", "-Wno-return-type", "main.cpp"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr[-3000:]


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
@pytest.mark.parametrize("spec", SIGNATURES, ids=[s["name"] for s in SIGNATURES])
def test_javascript_starter_loads(spec, tmp_path):
    source = drivers.program("javascript", spec, drivers.starter("javascript", spec))["main.js"]
    (tmp_path / "main.js").write_text(source, encoding="utf-8")
    proc = subprocess.run(["node", "--check", "main.js"], cwd=tmp_path, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr[-3000:]


@pytest.mark.parametrize("spec", SIGNATURES, ids=[s["name"] for s in SIGNATURES])
def test_python_starter_compiles(spec):
    source = drivers.program("python", spec, drivers.starter("python", spec))["main.py"]
    compile(source, "main.py", "exec")
