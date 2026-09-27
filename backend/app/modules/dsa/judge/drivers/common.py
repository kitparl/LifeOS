"""Shared driver types.

Every driver reads `tests.json` (a JSON array of test inputs), runs the user's code on each input
in order, and writes one JSON line per test to `result.jsonl`, flushing after each line:
    {"i": 0, "ok": true, "out": <json>, "ms": 1.25}
    {"i": 1, "ok": false, "err": "IndexError: list index out of range"}
The sandbox status explains a missing line (TLE / MLE / crash); see verdict.py.
"""

from typing import Any

# Plain signature dict (SignatureSpec.model_dump()); drivers never import pydantic models.
Spec = dict[str, Any]
# {filename: source} copied into the sandbox.
ProgramFiles = dict[str, str]


def scalar_and_depth(type_: str) -> tuple[str, int]:
    """'int[][]' -> ('int', 2); 'ListNode' -> ('ListNode', 0)."""
    depth = 0
    while type_.endswith("[]"):
        type_ = type_[:-2]
        depth += 1
    return type_, depth


def hidden_params(spec: Spec) -> set[str]:
    """Params that only describe test structure (link directives); not passed to user code."""
    hidden = set()
    for link in spec.get("links") or []:
        if link["kind"] == "cycle":
            hidden.add(link["pos"])
        elif link["kind"] == "join":
            hidden.add(link["shared"])
    return hidden


def visible_params(spec: Spec) -> list[dict[str, Any]]:
    hidden = hidden_params(spec)
    return [p for p in spec["params"] if p["name"] not in hidden]


def mutate_hint(spec: Spec) -> str | None:
    """Starter-code comment for in-place problems, or None."""
    target = spec.get("mutates")
    if not target:
        return None
    if spec["returns"] == "void":
        return f"Do not return anything, modify {target} in-place."
    return f"Modify {target} in-place and return the count of meaningful leading elements."
