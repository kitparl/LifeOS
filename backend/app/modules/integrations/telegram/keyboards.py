"""Inline keyboard builders for Telegram Bot API reply_markup."""

from __future__ import annotations

from typing import Any


def button(text: str, callback_data: str) -> dict[str, str]:
    """Single inline keyboard button. callback_data must be ≤64 bytes."""
    if len(callback_data.encode("utf-8")) > 64:
        raise ValueError(f"callback_data exceeds 64 bytes: {callback_data!r}")
    return {"text": text, "callback_data": callback_data}


def inline_keyboard(rows: list[list[dict[str, str]]]) -> dict[str, Any]:
    return {"inline_keyboard": rows}


def row(*buttons: dict[str, str]) -> list[dict[str, str]]:
    return list(buttons)


def nav_row(*, back: str | None = None, home: bool = True, refresh: str | None = None) -> list[dict[str, str]]:
    """Standard footer: Back / Refresh / Home."""
    buttons: list[dict[str, str]] = []
    if back:
        buttons.append(button("⬅ Back", back))
    if refresh:
        buttons.append(button("🔄 Refresh", refresh))
    if home:
        buttons.append(button("🏠 Home", "nav:home"))
    return buttons


def pagination_row(
    *,
    namespace: str,
    page: int,
    total_pages: int,
    extra: str = "",
) -> list[dict[str, str]]:
    """Prev / page indicator / Next. namespace is e.g. 'task' → task:page:N."""
    buttons: list[dict[str, str]] = []
    suffix = f":{extra}" if extra else ""
    if page > 0:
        buttons.append(button("◀", f"{namespace}:page:{page - 1}{suffix}"))
    buttons.append(button(f"{page + 1}/{total_pages}", f"{namespace}:noop"))
    if page < total_pages - 1:
        buttons.append(button("▶", f"{namespace}:page:{page + 1}{suffix}"))
    return buttons
