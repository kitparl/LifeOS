"""Habits interactive screens (Phase 2)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.habits.service import HabitService
from app.modules.integrations import telegram_templates as tpl
from app.modules.integrations.telegram import keyboards as kb
from app.modules.integrations.telegram.callbacks import CallbackContext, register
from app.modules.integrations.telegram.ids import resolve_one, short_id
from app.modules.integrations.telegram.navigation import back_home
from app.modules.integrations.telegram.renderer import Screen


async def habits_list_screen(db: AsyncSession, user_id: str) -> Screen:
    habits = await HabitService(db).list_habits(user_id, active_only=True)
    if not habits:
        return Screen(
            text=tpl.join_blocks(tpl._header("Habits"), "No active habits."),
            keyboard=kb.inline_keyboard([back_home(refresh="habit:list")]),
        )

    lines = []
    rows: list[list[dict]] = []
    for h in habits:
        sid = short_id(h.id)
        check = "✅" if h.completed_today else "⬜"
        streak = getattr(h, "streak", 0) or 0
        lines.append(
            f"{check} <b>{tpl.esc(h.name)}</b> · 🔥{streak} · <i>{tpl.esc(h.frequency)}</i>"
        )
        if not h.completed_today:
            rows.append(kb.row(kb.button(f"✅ {h.name[:28]}", f"habit:done:{sid}")))
        else:
            rows.append(kb.row(kb.button(f"↩️ Undo {h.name[:24]}", f"habit:undo:{sid}")))

    rows.append(back_home(refresh="habit:list"))
    due = sum(1 for h in habits if not h.completed_today)
    text = tpl.join_blocks(
        tpl._header("Habits", f"{due} remaining today"),
        "\n".join(lines),
    )
    return Screen(text=text, keyboard=kb.inline_keyboard(rows))


@register("habit", "list")
async def on_list(ctx: CallbackContext) -> Screen:
    return await habits_list_screen(ctx.db, ctx.user_id)


@register("habit", "done")
async def on_done(ctx: CallbackContext) -> tuple[Screen, str]:
    token = ctx.args[0] if ctx.args else ""
    habits = await HabitService(ctx.db).list_habits(ctx.user_id, active_only=True)
    habit = resolve_one(list(habits), token)
    if habit is None:
        return await habits_list_screen(ctx.db, ctx.user_id), "Not found"
    await HabitService(ctx.db).complete_today(ctx.user_id, habit.id)
    return await habits_list_screen(ctx.db, ctx.user_id), f"Done: {habit.name[:40]}"


@register("habit", "undo")
async def on_undo(ctx: CallbackContext) -> tuple[Screen, str]:
    token = ctx.args[0] if ctx.args else ""
    habits = await HabitService(ctx.db).list_habits(ctx.user_id, active_only=True)
    habit = resolve_one(list(habits), token)
    if habit is None:
        return await habits_list_screen(ctx.db, ctx.user_id), "Not found"
    await HabitService(ctx.db).uncomplete_today(ctx.user_id, habit.id)
    return await habits_list_screen(ctx.db, ctx.user_id), "Undone"
