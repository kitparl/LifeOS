"""Reference solutions for custom Run cases: lookup by slug, and the self-contained sandbox program."""

import json
import subprocess
import sys
from functools import cache
from pathlib import Path

import pytest
from app.modules.dsa.content.references import Reference, _registry, find_reference, reference_program
from app.modules.dsa.judge.compare import outputs_match
from app.modules.dsa.judge.runner import RESULT_FILE, parse_results

SEEDS = Path(__file__).resolve().parents[1] / "modules" / "dsa" / "seeds"


@cache
def _seed_problems() -> dict[str, dict]:
    problems: dict[str, dict] = {}
    for path in sorted(SEEDS.glob("p*.json")):
        for problem in json.loads(path.read_text(encoding="utf-8"))["problems"]:
            problems[problem["slug"]] = problem
    return problems


def _coverage_slugs() -> list[str]:
    """One problem per source module, plus every class, in-place and linked-input problem."""
    chosen: dict[str, str] = {}
    extra: list[str] = []
    for slug, (reference, signature) in sorted(_registry().items()):
        chosen.setdefault(reference.module, slug)
        if signature["kind"] == "class" or signature.get("mutates") or signature.get("links"):
            extra.append(slug)
    return sorted(set(chosen.values()) | set(extra))


def test_finds_reference_by_slug():
    problem = _seed_problems()["sum-of-square-numbers"]
    assert find_reference("sum-of-square-numbers", problem["signature"]) == Reference(
        "app.modules.dsa.content.sources.p01_two_pointers_b", "_judge_square_sum"
    )


def test_changed_or_unknown_problem_has_no_reference():
    signature = _seed_problems()["sum-of-square-numbers"]["signature"]
    assert find_reference("sum-of-square-numbers", {**signature, "returns": "int"}) is None
    assert find_reference("sum-of-square-numbers", None) is None
    assert find_reference("no-such-problem", signature) is None


@pytest.mark.parametrize("slug", _coverage_slugs())
def test_reference_program_reproduces_seed_outputs(slug, tmp_path):
    problem = _seed_problems()[slug]
    samples = [t for t in problem["tests"] if t["is_sample"]]
    reference = find_reference(slug, problem["signature"])
    assert reference is not None
    for name, content in reference_program(reference, problem["signature"]).items():
        (tmp_path / name).write_text(content, encoding="utf-8")
    (tmp_path / "tests.json").write_text(json.dumps([t["input"] for t in samples]), encoding="utf-8")

    # -I: the backend package is not importable, so the program must carry everything it needs.
    proc = subprocess.run([sys.executable, "-I", "main.py"], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr

    cases = parse_results((tmp_path / RESULT_FILE).read_text(encoding="utf-8"))
    assert [c.err for c in cases if not c.ok] == []
    assert len(cases) == len(samples)
    # Seeds store unordered outputs canonicalized, so compare the way the judge does.
    for case, test in zip(cases, samples, strict=True):
        assert outputs_match(
            problem["compare_mode"], test["expected"], case.out, checker_name=problem["checker"], test_input=test["input"]
        ), (test["input"], case.out)
