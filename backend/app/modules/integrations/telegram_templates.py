"""Telegram HTML message templates for LifeOS bot replies and digests.

All templates return strings safe for Telegram Bot API parse_mode=HTML.
Edit this file to change how the bot looks in chat.
"""

from __future__ import annotations

import html
from datetime import date, datetime


def esc(value: object) -> str:
    return html.escape(str(value), quote=False)


def _header(title: str, subtitle: str | None = None) -> str:
    if subtitle:
        return f"<b>{esc(title)}</b>\n<i>{esc(subtitle)}</i>"
    return f"<b>{esc(title)}</b>"


def _bullets(items: list[str], *, limit: int = 20) -> str:
    if not items:
        return ""
    lines = [f"• {esc(item)}" for item in items[:limit]]
    if len(items) > limit:
        lines.append(f"• …and {len(items) - limit} more")
    return "\n".join(lines)


def _section(title: str, body: str) -> str:
    if not body:
        return ""
    return f"<b>{esc(title)}</b>\n{body}"


def join_blocks(*blocks: str) -> str:
    return "\n\n".join(b.strip() for b in blocks if b and b.strip())


# --- Command templates ---


def help_message() -> str:
    return join_blocks(
        _header("LifeOS", "Bot commands"),
        (
            "<b>/add-task</b> <code>&lt;title&gt;</code> — create a task (due today by default)\n"
            "<b>/tasks</b> — pending tasks\n"
            "<b>/today</b> — today's agenda\n"
            "<b>/done</b> <code>&lt;id&gt;</code> — complete a task\n"
            "<b>/habits</b> — habits due\n"
            "<b>/goals</b> — active goals\n"
            "<b>/help</b> — this message"
        ),
    )


def hint_send_command() -> str:
    return join_blocks(
        _header("LifeOS"),
        "Send a command like <b>/help</b> to get started.",
    )


def unknown_command(cmd: str) -> str:
    return join_blocks(
        _header("Unknown command"),
        f"<code>{esc(cmd)}</code>\nTry <b>/help</b> for the list.",
    )


def unrecognized_command() -> str:
    return join_blocks(_header("Unrecognized command"), "Try <b>/help</b>.")


def command_error() -> str:
    return join_blocks(
        _header("Something went wrong"),
        "Sorry — that command failed. Try again in a moment.",
    )


def tasks_empty() -> str:
    return join_blocks(_header("Pending tasks"), "No pending tasks. Nice work!")


def tasks_list(lines: list[str], *, total: int) -> str:
    body = _bullets(lines, limit=20)
    extra = f"\n\n<i>Showing {min(total, 20)} of {total}</i>" if total > 20 else ""
    return join_blocks(_header("Pending tasks", f"{total} open"), body) + extra


def task_line(*, short_id: str, title: str, status: str, due: str) -> str:
    return f"[{short_id}] {title} ({status}, {due})"


def today_empty(day: date) -> str:
    return join_blocks(
        _header("Today", day.isoformat()),
        "Nothing scheduled for today.",
    )


def today_agenda(
    day: date,
    *,
    tasks: list[str],
    calendar: list[str],
    races: list[str],
) -> str:
    blocks = [_header("Today", day.isoformat())]
    if tasks:
        blocks.append(_section("Tasks due today", _bullets(tasks, limit=10)))
    if calendar:
        blocks.append(_section("Calendar", _bullets(calendar, limit=10)))
    if races:
        blocks.append(_section("Races", _bullets(races, limit=10)))
    if len(blocks) == 1:
        return today_empty(day)
    return join_blocks(*blocks)


def done_usage() -> str:
    return join_blocks(
        _header("Complete a task"),
        "Usage: <b>/done</b> <code>&lt;task_id_prefix&gt;</code>\n"
        "Get ids from <b>/tasks</b> (the 8-character code in brackets).",
    )


def add_task_usage() -> str:
    return join_blocks(
        _header("Add a task"),
        "Usage:\n"
        "<b>/add-task</b> <code>&lt;title&gt;</code>\n"
        "<b>/add-task</b> <code>&lt;title&gt; due YYYY-MM-DD</code>\n"
        "<b>/add-task</b> <code>&lt;title&gt; tomorrow</code>\n\n"
        "Default due date: <b>today</b>\n"
        "Examples:\n"
        "<code>/add-task Buy milk</code>\n"
        "<code>/add-task Call dentist due 2026-08-01</code>\n"
        "<code>/add-task Pay rent tomorrow</code>",
    )


def add_task_success(*, short_id: str, title: str, due: str) -> str:
    return join_blocks(
        _header("Task created"),
        f"<code>[{esc(short_id)}]</code> {esc(title)}\n"
        f"Due: <b>{esc(due)}</b>\n\n"
        f"Complete later with <b>/done</b> <code>{esc(short_id)}</code>",
    )


def add_task_too_long() -> str:
    return join_blocks(
        _header("Title too long"),
        "Keep the task title under 200 characters.",
    )


def add_task_bad_due(token: str) -> str:
    return join_blocks(
        _header("Invalid due date"),
        f"Could not parse <code>{esc(token)}</code>.\n"
        "Use <code>YYYY-MM-DD</code>, <code>today</code>, or <code>tomorrow</code>.",
    )


def done_not_found(token: str) -> str:
    return join_blocks(
        _header("Not found"),
        f"No open task matching <code>{esc(token)}</code>.",
    )


def done_ambiguous(lines: list[str]) -> str:
    return join_blocks(
        _header("Ambiguous id"),
        "Matches more than one task — be more specific:",
        _bullets(lines, limit=5),
    )


def done_success(title: str) -> str:
    return join_blocks(_header("Done"), esc(title))


def habits_empty() -> str:
    return join_blocks(
        _header("Habits due"),
        "All active habits completed for this period.",
    )


def habits_list(lines: list[str]) -> str:
    return join_blocks(
        _header("Habits due", f"{len(lines)} remaining"),
        _bullets(lines, limit=20),
    )


def goals_empty() -> str:
    return join_blocks(_header("Active goals"), "No active goals.")


def goals_list(lines: list[str]) -> str:
    return join_blocks(
        _header("Active goals", f"{len(lines)} active"),
        _bullets(lines, limit=15),
    )


# --- Digest template ---


def digest_message(
    *,
    stamp: datetime | str,
    pending_tasks: list[str],
    upcoming_events: list[str],
    upcoming_races: list[str],
    habits_due: list[str],
    active_goals: list[str],
) -> str:
    if isinstance(stamp, datetime):
        stamp_s = stamp.strftime("%Y-%m-%d %H:%M UTC")
    else:
        stamp_s = str(stamp)

    sections: list[tuple[str, list[str]]] = [
        ("Pending tasks", pending_tasks),
        ("Upcoming calendar", upcoming_events),
        ("Upcoming races", upcoming_races),
        ("Habits due", habits_due),
        ("Active goals", active_goals),
    ]
    if not any(items for _, items in sections):
        return join_blocks(
            _header("LifeOS Digest", stamp_s),
            "Nothing pending — you're all caught up.",
        )

    blocks = [_header("LifeOS Digest", stamp_s)]
    for title, items in sections:
        if not items:
            continue
        blocks.append(
            _section(f"{title} ({len(items)})", _bullets(items, limit=15))
        )
    return join_blocks(*blocks)


# --- Outbound event push templates (optional reuse) ---


def event_task_created(title: str, due: str | None = None) -> str:
    due_bit = f" (due {esc(due)})" if due else ""
    return join_blocks(_header("New task"), f"{esc(title)}{due_bit}")


def event_generic(title: str, body: str) -> str:
    return join_blocks(_header(title), esc(body))


def test_connection_message() -> str:
    return join_blocks(
        _header("LifeOS"),
        "Telegram connection test succeeded.",
    )
