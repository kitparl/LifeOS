"""Python driver: embeds codec.py (in its own namespace) + common imports + user code + test loop."""

from __future__ import annotations

import inspect
import json

from app.modules.dsa.judge import codec
from app.modules.dsa.judge.drivers.common import ProgramFiles, Spec, mutate_hint, visible_params

_TYPES = {
    "int": "int",
    "long": "int",
    "double": "float",
    "bool": "bool",
    "string": "str",
    "char": "str",
    "ListNode": "Optional[ListNode]",
    "ListNode[]": "List[Optional[ListNode]]",
    "TreeNode": "Optional[TreeNode]",
    "void": "None",
}

_PREAMBLE = """\
import sys, math, heapq, bisect, itertools, functools, collections, string, re
from typing import *
from collections import *
from functools import lru_cache, cache, reduce, cmp_to_key
from heapq import *
from bisect import *
from itertools import *
from math import inf
"""

_MAIN = """
def _dsa_main():
    import json, time
    spec = json.loads(_DSA_SPEC)
    with open("tests.json", encoding="utf-8") as fh:
        tests = json.load(fh)
    with open("result.jsonl", "w", encoding="utf-8") as out:
        for i, test in enumerate(tests):
            try:
                if spec["kind"] == "function":
                    target = getattr(Solution(), spec["name"])
                else:
                    target = globals()[spec["name"]]
                start = time.perf_counter()
                result = _dsa["invoke"](spec, target, test)
                ms = (time.perf_counter() - start) * 1000.0
                line = json.dumps({"i": i, "ok": True, "out": result, "ms": round(ms, 3)}, allow_nan=False)
            except BaseException as exc:  # user code may raise anything, including SystemExit
                line = json.dumps({"i": i, "ok": False, "err": (type(exc).__name__ + ": " + str(exc))[:500]})
            out.write(line + "\\n")
            out.flush()


import threading as _dsa_threading
sys.setrecursionlimit(200000)
_dsa_threading.stack_size(256 * 1024 * 1024)
_dsa_thread = _dsa_threading.Thread(target=_dsa_main)
_dsa_thread.start()
_dsa_thread.join()
"""


def _py_type(type_: str) -> str:
    if type_ in _TYPES:
        return _TYPES[type_]
    return f"List[{_py_type(type_[:-2])}]"


def _params(params: list[dict]) -> str:
    return ", ".join(f"{p['name']}: {_py_type(p['type'])}" for p in params)


def starter(spec: Spec) -> str:
    if spec["kind"] == "function":
        args = _params(visible_params(spec))
        hint = mutate_hint(spec)
        body = f'        """{hint}"""\n' if hint else ""
        return (
            "class Solution:\n"
            f"    def {spec['name']}(self, {args}) -> {_py_type(spec['returns'])}:\n"
            f"{body}        pass\n"
        )
    ctor = _params(spec["constructor"])
    lines = [f"class {spec['name']}:", "", f"    def __init__(self{', ' + ctor if ctor else ''}):", "        pass", ""]
    for m in spec["methods"]:
        margs = _params(m["params"])
        lines += [
            f"    def {m['name']}(self{', ' + margs if margs else ''}) -> {_py_type(m['returns'])}:",
            "        pass",
            "",
        ]
    return "\n".join(lines).rstrip() + "\n"


def program(spec: Spec, user_code: str) -> ProgramFiles:
    codec_source = inspect.getsource(codec)
    source = (
        f"_DSA_CODEC = {codec_source!r}\n"
        "_dsa = {}\n"
        "exec(_DSA_CODEC, _dsa)\n"
        'ListNode = _dsa["ListNode"]\n'
        'TreeNode = _dsa["TreeNode"]\n'
        f"_DSA_SPEC = {json.dumps(spec)!r}\n"
        f"{_PREAMBLE}\n"
        "# ---- user code ----\n"
        f"{user_code}\n"
        "# ---- end user code ----\n"
        f"{_MAIN}"
    )
    return {"main.py": source}
