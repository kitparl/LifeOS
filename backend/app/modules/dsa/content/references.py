"""Reference solutions for checking custom Run cases.

`find_reference` maps a problem to the reference solution its seed was built from, and
`reference_program` turns it into a self-contained Python program for the sandbox: the source
module, the sibling sources it imports, `content/model.py` and `judge/codec.py` are embedded and
served by an in-memory import hook. The API process only looks references up; it never calls one.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.modules.dsa.content.build import discover_sources, load_catalog
from app.modules.dsa.judge.signature import parse_spec

_SOURCES_PACKAGE = "app.modules.dsa.content.sources"
_BASE_MODULES = ("app.modules.dsa.content.model", "app.modules.dsa.judge.codec")
_SOURCE_IMPORT = re.compile(rf"^from ({re.escape(_SOURCES_PACKAGE)}\.\w+) import", re.MULTILINE)


@dataclass(frozen=True)
class Reference:
    module: str
    name: str


@lru_cache(maxsize=1)
def _registry() -> dict[str, tuple[Reference, dict]]:
    """slug -> (reference, the signature the seed was built with), paired the way the build pairs them."""
    slugs = {(p["pattern"], p["title"]): p["slug"] for p in load_catalog()["problems"]}
    registry: dict[str, tuple[Reference, dict]] = {}
    for pattern in discover_sources():
        for source in pattern.problems:
            slug = slugs.get((pattern.number, source.title))
            target = source.reference
            module, name = target.__module__, target.__qualname__
            if slug is None or "." in name or getattr(sys.modules.get(module), name, None) is not target:
                continue  # only module-level functions/classes can be imported by name in the sandbox
            registry[slug] = (Reference(module, name), parse_spec(source.signature).model_dump(exclude_none=True))
    return registry


def find_reference(slug: str, signature: dict | None) -> Reference | None:
    """The problem's reference, unless it has none or its signature was changed since the seed."""
    entry = _registry().get(slug)
    if entry is None or signature is None or entry[1] != signature:
        return None
    return entry[0]


def _module_source(name: str) -> str:
    spec = importlib.util.find_spec(name)
    assert spec is not None and spec.origin is not None
    return Path(spec.origin).read_text(encoding="utf-8")


def _embedded_modules(module: str) -> dict[str, str]:
    """The target module, the sibling sources it imports (transitively), and the shared modules."""
    modules = {name: _module_source(name) for name in _BASE_MODULES}
    pending = [module]
    while pending:
        name = pending.pop()
        if name in modules:
            continue
        modules[name] = _module_source(name)
        pending += _SOURCE_IMPORT.findall(modules[name])
    return modules


_PROGRAM = '''\
import importlib.abc, importlib.util, json, sys, threading, time

_DSA_MODULES = json.loads(_DSA_MODULES_JSON)
_DSA_PACKAGES = {n.rsplit(".", k)[0] for n in _DSA_MODULES for k in range(1, n.count(".") + 1)}


class _DsaImporter(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, name, path=None, target=None):
        if name in _DSA_MODULES or name in _DSA_PACKAGES:
            return importlib.util.spec_from_loader(name, self, is_package=name in _DSA_PACKAGES)
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        exec(compile(_DSA_MODULES.get(module.__name__, ""), module.__name__, "exec"), module.__dict__)


sys.meta_path.insert(0, _DsaImporter())


def _dsa_main():
    spec = json.loads(_DSA_SPEC_JSON)
    codec = importlib.import_module("app.modules.dsa.judge.codec")
    target = getattr(importlib.import_module(_DSA_TARGET[0]), _DSA_TARGET[1])
    with open("tests.json", encoding="utf-8") as fh:
        tests = json.load(fh)
    with open("result.jsonl", "w", encoding="utf-8") as out:
        for i, test in enumerate(tests):
            try:
                start = time.perf_counter()
                result = codec.invoke(spec, target, test)
                ms = (time.perf_counter() - start) * 1000.0
                line = json.dumps({"i": i, "ok": True, "out": result, "ms": round(ms, 3)}, allow_nan=False)
            except BaseException as exc:
                line = json.dumps({"i": i, "ok": False, "err": (type(exc).__name__ + ": " + str(exc))[:500]})
            out.write(line + "\\n")
            out.flush()


sys.setrecursionlimit(200000)
threading.stack_size(256 * 1024 * 1024)
_dsa_thread = threading.Thread(target=_dsa_main)
_dsa_thread.start()
_dsa_thread.join()
'''


def reference_program(reference: Reference, spec: dict) -> dict[str, str]:
    """Files for a sandbox run of the reference over `tests.json` (added by the caller)."""
    header = (
        f"_DSA_MODULES_JSON = {json.dumps(_embedded_modules(reference.module))!r}\n"
        f"_DSA_SPEC_JSON = {json.dumps(spec)!r}\n"
        f"_DSA_TARGET = {(reference.module, reference.name)!r}\n"
    )
    return {"main.py": header + _PROGRAM}
