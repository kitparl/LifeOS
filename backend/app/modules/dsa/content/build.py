"""Build seed JSON from content sources: run every reference solution to produce expected outputs.

Usage (from backend/):
    python -m app.modules.dsa.content.build                # all patterns with sources
    python -m app.modules.dsa.content.build --pattern 1    # one pattern
    python -m app.modules.dsa.content.build --check        # fail if seeds/ is out of date

The output is deterministic (fixed per-problem RNG seed, sorted keys), so re-running on unchanged
sources produces byte-identical files.
"""

from __future__ import annotations

import argparse
import copy
import importlib
import json
import pkgutil
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from pydantic import ValidationError

from app.modules.dsa.content import sources
from app.modules.dsa.content.model import ProblemSource, TestInput
from app.modules.dsa.judge import codec
from app.modules.dsa.judge.compare import CHECKERS, COMPARE_MODES, outputs_match
from app.modules.dsa.judge.signature import SignatureError, parse_spec, validate_expected, validate_input

SEEDS_DIR = Path(__file__).resolve().parent.parent / "seeds"
CATALOG_PATH = SEEDS_DIR / "catalog.json"
BASE_SEED = 20260926
MAX_TESTS = 40
MAX_SUITE_BYTES = 200 * 1024
MAX_TEST_INPUT_BYTES = 32 * 1024


class ContentError(ValueError):
    """A problem source is invalid or its reference solution misbehaves."""


@dataclass(frozen=True)
class PatternSource:
    number: int
    problems: list[ProblemSource]
    module_name: str


def load_catalog(path: Path = CATALOG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_sources() -> list[PatternSource]:
    """One PatternSource per pattern number; modules declaring the same number are merged."""
    merged: dict[int, PatternSource] = {}
    for info in sorted(pkgutil.iter_modules(sources.__path__), key=lambda i: i.name):
        module = importlib.import_module(f"{sources.__name__}.{info.name}")
        part = _pattern_source(module)
        if part.number in merged:
            prev = merged[part.number]
            part = PatternSource(part.number, prev.problems + part.problems, f"{prev.module_name},{part.module_name}")
        merged[part.number] = part
    return [merged[n] for n in sorted(merged)]


def _pattern_source(module: ModuleType) -> PatternSource:
    try:
        return PatternSource(int(module.PATTERN_NUMBER), list(module.PROBLEMS), module.__name__)
    except AttributeError as exc:
        raise ContentError(f"{module.__name__} must define PATTERN_NUMBER and PROBLEMS") from exc


def build_pattern(pattern: PatternSource, catalog: dict[str, Any]) -> dict[str, Any]:
    entries = {p["title"]: p for p in catalog["problems"] if p["pattern"] == pattern.number}
    if not entries:
        raise ContentError(f"pattern {pattern.number} is not in the catalog")
    built = []
    for source in pattern.problems:
        entry = entries.get(source.title)
        if entry is None:
            raise ContentError(f"{source.title!r} is not a catalog title of pattern {pattern.number}")
        built.append((entry["order"], build_problem(source, entry["slug"])))
    slugs = [p["slug"] for _, p in built]
    if len(slugs) != len(set(slugs)):
        raise ContentError(f"pattern {pattern.number} defines a problem twice")
    return {"pattern": pattern.number, "problems": [p for _, p in sorted(built, key=lambda x: x[0])]}


def build_problem(source: ProblemSource, slug: str) -> dict[str, Any]:
    where = f"{slug}:"
    try:
        spec = parse_spec(source.signature)
    except ValidationError as exc:
        raise ContentError(f"{where} invalid signature: {exc}") from exc
    if source.compare not in COMPARE_MODES:
        raise ContentError(f"{where} unknown compare mode {source.compare!r}")
    if source.compare == "checker" and source.checker not in CHECKERS:
        raise ContentError(f"{where} unknown checker {source.checker!r}")
    if not 2 <= len(source.examples) <= 3:
        raise ContentError(f"{where} needs 2-3 examples")
    if not source.statement.strip() or not source.constraints.strip():
        raise ContentError(f"{where} statement and constraints are required")

    spec_dict = spec.model_dump(exclude_none=True)
    rng = random.Random(f"{BASE_SEED}:{slug}")
    planned: list[tuple[TestInput, str, str | None]] = [(e.input, "example", e.explanation) for e in source.examples]
    planned += [(case, "edge", None) for case in source.edge_cases]
    if source.random_count and source.generator is None:
        raise ContentError(f"{where} random_count needs a generator")
    planned += [(_draw(source, rng, where), "random", None) for _ in range(source.random_count)] if source.generator else []

    tests, seen = [], set()
    for test_input, kind, explanation in planned:
        key = json.dumps(test_input, sort_keys=True)
        if key in seen:
            if kind == "example":
                raise ContentError(f"{where} duplicate example")
            continue
        seen.add(key)
        if len(key) > MAX_TEST_INPUT_BYTES:
            raise ContentError(f"{where} a {kind} input is {len(key)} bytes (max {MAX_TEST_INPUT_BYTES})")
        expected = _expected(source, spec_dict, spec, test_input, where)
        if source.brute is not None and (kind == "example" or len(key) <= source.brute_input_limit):
            _cross_check(source, spec_dict, test_input, expected, where)
        tests.append(
            {
                "input": test_input,
                "expected": expected,
                "is_sample": kind == "example",
                "kind": kind,
                "explanation": explanation,
            }
        )
    if len(tests) > MAX_TESTS:
        raise ContentError(f"{where} {len(tests)} tests (max {MAX_TESTS})")
    if len(json.dumps(tests)) > MAX_SUITE_BYTES:
        raise ContentError(f"{where} test suite exceeds {MAX_SUITE_BYTES} bytes")

    return {
        "slug": slug,
        "title": source.title,
        "is_variant": source.is_variant,
        "statement": source.statement.strip() + "\n",
        "constraints": source.constraints.strip() + "\n",
        "signature": spec_dict,
        "compare_mode": source.compare,
        "checker": source.checker,
        "time_limit_ms": source.time_limit_ms,
        "memory_limit_mb": source.memory_limit_mb,
        "tests": tests,
    }


def _draw(source: ProblemSource, rng: random.Random, where: str) -> TestInput:
    """One generated input within the size cap (redrawn, deterministically, if too large)."""
    assert source.generator is not None
    for _ in range(20):
        test_input = source.generator(rng)
        if len(json.dumps(test_input, sort_keys=True)) <= MAX_TEST_INPUT_BYTES:
            return test_input
    raise ContentError(f"{where} generator keeps producing inputs over {MAX_TEST_INPUT_BYTES} bytes")


def _expected(source: ProblemSource, spec_dict: dict, spec: Any, test_input: TestInput, where: str) -> Any:
    try:
        validate_input(spec, test_input)
    except SignatureError as exc:
        raise ContentError(f"{where} bad input {_short(test_input)}: {exc}") from exc
    try:
        first = codec.invoke(spec_dict, source.reference, copy.deepcopy(test_input))
        second = codec.invoke(spec_dict, source.reference, copy.deepcopy(test_input))
    except Exception as exc:
        raise ContentError(f"{where} reference failed on {_short(test_input)}: {type(exc).__name__}: {exc}") from exc
    try:
        validate_expected(spec, first, test_input)
    except SignatureError as exc:
        raise ContentError(f"{where} reference output invalid on {_short(test_input)}: {exc}") from exc
    if not outputs_match(source.compare, first, second, checker_name=source.checker, test_input=test_input):
        raise ContentError(f"{where} reference is not deterministic on {_short(test_input)}")
    return _canonical(source.compare, first)


def _canonical(mode: str, value: Any) -> Any:
    """Order-insensitive answers are stored sorted, so seeds don't depend on set/hash iteration order."""
    if mode == "unordered" and isinstance(value, list):
        return sorted(value, key=_canon_key)
    if mode == "unordered_nested" and isinstance(value, list):
        return sorted((sorted(v, key=_canon_key) if isinstance(v, list) else v for v in value), key=_canon_key)
    return value


def _canon_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


class _BruteSkipped(Exception):
    """The brute returned NotImplemented for this input."""


def _skippable(brute: Any) -> Any:
    if isinstance(brute, type):  # design problems: a class, never skipped
        return brute

    def call(*args: Any) -> Any:
        out = brute(*args)
        if out is NotImplemented:
            raise _BruteSkipped
        return out

    return call


def _cross_check(source: ProblemSource, spec_dict: dict, test_input: TestInput, expected: Any, where: str) -> None:
    assert source.brute is not None
    try:
        brute_out = codec.invoke(spec_dict, _skippable(source.brute), copy.deepcopy(test_input))
    except _BruteSkipped:
        return
    except Exception as exc:
        raise ContentError(f"{where} brute failed on {_short(test_input)}: {type(exc).__name__}: {exc}") from exc
    if not outputs_match(source.compare, expected, brute_out, checker_name=source.checker, test_input=test_input):
        raise ContentError(
            f"{where} reference and brute disagree on {_short(test_input)}: {_short(expected)} vs {_short(brute_out)}"
        )


def _short(value: Any, limit: int = 120) -> str:
    text = json.dumps(value)
    return text if len(text) <= limit else text[:limit] + "..."


def render(seed: dict[str, Any]) -> str:
    """Deterministic JSON: one line per problem header and one compact line per test case."""
    problems = []
    for problem in seed["problems"]:
        meta = json.dumps({k: v for k, v in problem.items() if k != "tests"}, sort_keys=True, ensure_ascii=False)
        tests = ",\n".join(
            json.dumps(t, sort_keys=True, ensure_ascii=False, separators=(",", ":")) for t in problem["tests"]
        )
        problems.append(f'{meta[:-1]}, "tests": [\n{tests}\n]}}')
    return f'{{"pattern": {seed["pattern"]}, "problems": [\n' + ",\n".join(problems) + "\n]}\n"


def seed_path(pattern_number: int, catalog: dict[str, Any]) -> Path:
    slug = next(p["slug"] for p in catalog["patterns"] if p["number"] == pattern_number)
    return SEEDS_DIR / f"p{pattern_number:02d}-{slug}.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build DSA seed JSON from content sources")
    parser.add_argument("--pattern", type=int, help="only this pattern number")
    parser.add_argument("--check", action="store_true", help="verify seeds are up to date; write nothing")
    args = parser.parse_args(argv)

    catalog = load_catalog()
    patterns = [p for p in discover_sources() if args.pattern is None or p.number == args.pattern]
    stale = []
    for pattern in patterns:
        path = seed_path(pattern.number, catalog)
        text = render(build_pattern(pattern, catalog))
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(path.name)
            continue
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.name} ({len(pattern.problems)} problems)")
    if stale:
        print("out of date: " + ", ".join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
