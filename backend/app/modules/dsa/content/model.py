"""Authoring format for problem content (see content/sources/*.py and the module README).

A source module exports `PATTERN_NUMBER: int` and `PROBLEMS: list[ProblemSource]`; a pattern may be
split across several modules (their PROBLEMS are merged). The build runs
each `reference` on every example, edge case and generated input to produce expected outputs, so
no expected output is ever typed by hand. Statements are original wording.
"""

from __future__ import annotations

import random
import string
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

TestInput = list[Any] | dict[str, list[Any]]
Generator = Callable[[random.Random], TestInput]


@dataclass(frozen=True)
class Example:
    input: TestInput
    explanation: str | None = None


@dataclass(frozen=True)
class ProblemSource:
    title: str
    statement: str
    constraints: str
    signature: dict[str, Any]
    # A function for function specs, a class for class specs; called with decoded arguments.
    reference: Callable[..., Any]
    examples: list[Example]
    edge_cases: list[TestInput] = field(default_factory=list)
    generator: Generator | None = None
    random_count: int = 0
    compare: str = "exact"
    checker: str | None = None
    time_limit_ms: int = 1000
    memory_limit_mb: int = 256
    # Course-specific titles with no single public definition get our own definition (D-03).
    is_variant: bool = False
    # Optional independent (usually brute-force) solution; the build cross-checks it against
    # `reference` on every example and on edge/random cases within `brute_input_limit`. A brute may
    # return `NotImplemented` to skip an input it can't check quickly.
    brute: Callable[..., Any] | None = None
    # Edge and random cases whose input JSON is at most this long are cross-checked against `brute`
    # (examples always are); lower it for exponential brutes.
    brute_input_limit: int = 1500


# ---------------------------------------------------------------- signature helpers


def function(
    name: str,
    params: list[tuple[str, str]],
    returns: str,
    *,
    mutates: str | None = None,
    links: list[dict[str, str]] | None = None,
    circular_output: bool = False,
) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "kind": "function",
        "name": name,
        "params": [{"name": n, "type": t} for n, t in params],
        "returns": returns,
    }
    if mutates is not None:
        spec["mutates"] = mutates
    if links:
        spec["links"] = links
    if circular_output:
        spec["circular_output"] = True
    return spec


def design(
    name: str, constructor: list[tuple[str, str]], methods: list[tuple[str, list[tuple[str, str]], str]]
) -> dict[str, Any]:
    return {
        "kind": "class",
        "name": name,
        "constructor": [{"name": n, "type": t} for n, t in constructor],
        "methods": [
            {"name": m, "params": [{"name": n, "type": t} for n, t in params], "returns": ret}
            for m, params, ret in methods
        ],
    }


def ops(*calls: tuple[str, list[Any]]) -> dict[str, list[Any]]:
    """Class-problem input from (op, args) pairs; the first pair is the constructor."""
    return {"ops": [c[0] for c in calls], "args": [c[1] for c in calls]}


# ---------------------------------------------------------------- generator helpers


def ints(rng: random.Random, n: int, lo: int, hi: int) -> list[int]:
    return [rng.randint(lo, hi) for _ in range(n)]


def sorted_ints(rng: random.Random, n: int, lo: int, hi: int) -> list[int]:
    return sorted(ints(rng, n, lo, hi))


def word(rng: random.Random, n: int, alphabet: str = string.ascii_lowercase) -> str:
    return "".join(rng.choice(alphabet) for _ in range(n))


def matrix(rng: random.Random, rows: int, cols: int, lo: int, hi: int) -> list[list[int]]:
    return [ints(rng, cols, lo, hi) for _ in range(rows)]


def pick_n(rng: random.Random, lo: int, hi: int, big: int | None = None) -> int:
    """Mostly small sizes (easy to debug, brute-checkable), sometimes medium, occasionally `big`."""
    r = rng.random()
    if big is not None and r < 0.2:
        return rng.randint(max(lo, big // 2), big)
    if r < 0.6:
        return rng.randint(lo, min(hi, lo + 10))
    return rng.randint(lo, hi)


def random_tree(rng: random.Random, n: int, lo: int, hi: int, *, unique: bool = False) -> list[int | None]:
    """Level-order JSON for a random binary tree with n nodes (random shape)."""
    if n == 0:
        return []
    values = rng.sample(range(lo, hi + 1), n) if unique else ints(rng, n, lo, hi)
    children: list[list[int | None]] = [[None, None]]
    free = [(0, 0), (0, 1)]
    for i in range(1, n):
        parent, side = free.pop(rng.randrange(len(free)))
        children[parent][side] = i
        children.append([None, None])
        free += [(i, 0), (i, 1)]
    out: list[int | None] = []
    queue: list[int | None] = [0]
    for node in queue:
        if node is None:
            out.append(None)
            continue
        out.append(values[node])
        queue.extend(children[node])
    while out and out[-1] is None:
        out.pop()
    return out


def sample(rng: random.Random, population: range | list, k: int) -> list:
    """rng.sample that never asks for more items than the population holds."""
    return rng.sample(population, min(k, len(population)))
