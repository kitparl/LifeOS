"""Driver registry: `starter(spec)` and `program(spec, user_code)` per language id."""

from types import ModuleType

from app.modules.dsa.judge.drivers import cpp, java, javascript, python
from app.modules.dsa.judge.drivers.common import ProgramFiles, Spec

_DRIVERS: dict[str, ModuleType] = {"python": python, "javascript": javascript, "cpp": cpp, "java": java}


def starter(language: str, spec: Spec) -> str:
    return _driver(language).starter(spec)


def program(language: str, spec: Spec, user_code: str) -> ProgramFiles:
    return _driver(language).program(spec, user_code)


def _driver(language: str) -> ModuleType:
    try:
        return _DRIVERS[language]
    except KeyError as exc:
        raise ValueError(f"unsupported language {language!r}") from exc


__all__: list[str] = ["ProgramFiles", "Spec", "program", "starter"]
