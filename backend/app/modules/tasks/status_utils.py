"""Task status normalization and helpers."""

from app.modules.tasks.models import TASK_STATUSES

_ALIAS = {"done": "completed"}


def normalize_task_status(raw: str | None) -> str | None:
    if raw is None:
        return None
    value = _ALIAS.get(str(raw).strip().lower(), str(raw).strip().lower())
    if value not in TASK_STATUSES:
        raise ValueError(
            f"Invalid task status '{raw}'. Allowed: {', '.join(TASK_STATUSES)} (alias: done)"
        )
    return value
