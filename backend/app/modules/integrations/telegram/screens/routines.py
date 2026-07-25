"""Routines screens (Phase 3) — read-only + skip-today via skip_dates."""

from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations import telegram_templates as tpl
from app.modules.integrations.telegram import keyboards as kb
from app.modules.integrations.telegram.callbacks import CallbackContext, register
from app.modules.integrations.telegram.ids import resolve_one, short_id
from app.modules.integrations.telegram.navigation import back_home
from app.modules.integrations.telegram.renderer import Screen
from app.modules.routines.schemas import RoutineUpdate
from app.modules.routines.service import RoutineService


async def routines_list_screen(db: AsyncSession, user_id: str) -> Screen:
    routines = await RoutineService(db).list_routines(user_id, active_only=True)
    if not routines:
        return Screen(
            text=tpl.join_blocks(tpl._header("Routines"), "No active routines."),
            keyboard=kb.inline_keyboard([back_home(refresh="routine:list")]),
        )
    lines = []
    rows: list[list[dict]] = []
    for r in routines:
        sid = short_id(r.id)
        count = getattr(r, "block_count", 0) or 0
        lines.append(f"• <b>{tpl.esc(r.name)}</b> · {count} blocks")
        rows.append(kb.row(kb.button(f"👁 {r.name[:28]}", f"routine:view:{sid}")))
    # Today preview
    preview = await RoutineService(db).today_preview(user_id, limit=6)
    if preview:
        lines.append("")
        lines.append("<b>Today</b>")
        for name, title, when, _rid in preview:
            hhmm = when.strftime("%H:%M") if when else "?"
            lines.append(f"• {tpl.esc(hhmm)} {tpl.esc(title)} <i>({tpl.esc(name)})</i>")

    rows.append(back_home(refresh="routine:list"))
    text = tpl.join_blocks(tpl._header("Routines", f"{len(routines)} active"), "\n".join(lines))
    return Screen(text=text, keyboard=kb.inline_keyboard(rows))


async def routine_detail_screen(db: AsyncSession, user_id: str, token: str) -> Screen:
    routines = await RoutineService(db).list_routines(user_id, active_only=False)
    summary = resolve_one(list(routines), token)
    if summary is None:
        return Screen(
            text=tpl.join_blocks(tpl._header("Not found"), "Routine not found."),
            keyboard=kb.inline_keyboard([back_home(back="routine:list")]),
        )
    routine = await RoutineService(db).get_routine(user_id, summary.id)
    sid = short_id(routine.id)
    today = date.today().isoformat()
    skipped = today in (routine.skip_dates or [])

    block_lines = []
    for b in routine.blocks or []:
        st = b.start_time.strftime("%H:%M") if hasattr(b.start_time, "strftime") else str(b.start_time)
        et = b.end_time.strftime("%H:%M") if hasattr(b.end_time, "strftime") else str(b.end_time)
        block_lines.append(f"• <b>{tpl.esc(st)}–{tpl.esc(et)}</b> {tpl.esc(b.title)}")
    status = f"⏭ Skipped today" if skipped else "Active today"
    text = tpl.join_blocks(
        tpl._header(routine.name, status),
        "\n".join(block_lines) if block_lines else "<i>No blocks</i>",
    )
    rows = []
    if skipped:
        rows.append(kb.row(kb.button("↩️ Unskip today", f"routine:unskip:{sid}")))
    else:
        rows.append(kb.row(kb.button("⏭ Skip today", f"routine:skip:{sid}")))
    rows.append(back_home(back="routine:list", refresh=f"routine:view:{sid}"))
    return Screen(text=text, keyboard=kb.inline_keyboard(rows))


@register("routine", "list")
async def on_list(ctx: CallbackContext) -> Screen:
    return await routines_list_screen(ctx.db, ctx.user_id)


@register("routine", "view")
async def on_view(ctx: CallbackContext) -> Screen:
    return await routine_detail_screen(ctx.db, ctx.user_id, ctx.args[0] if ctx.args else "")


@register("routine", "skip")
async def on_skip(ctx: CallbackContext) -> tuple[Screen, str]:
    token = ctx.args[0] if ctx.args else ""
    routines = await RoutineService(ctx.db).list_routines(ctx.user_id, active_only=False)
    summary = resolve_one(list(routines), token)
    if summary is None:
        return await routines_list_screen(ctx.db, ctx.user_id), "Not found"
    routine = await RoutineService(ctx.db).get_routine(ctx.user_id, summary.id)
    today = date.today().isoformat()
    skips = list(routine.skip_dates or [])
    if today not in skips:
        skips.append(today)
    await RoutineService(ctx.db).update_routine(
        ctx.user_id, routine.id, RoutineUpdate(skip_dates=skips)
    )
    return await routine_detail_screen(ctx.db, ctx.user_id, token), "Skipped today"


@register("routine", "unskip")
async def on_unskip(ctx: CallbackContext) -> tuple[Screen, str]:
    token = ctx.args[0] if ctx.args else ""
    routines = await RoutineService(ctx.db).list_routines(ctx.user_id, active_only=False)
    summary = resolve_one(list(routines), token)
    if summary is None:
        return await routines_list_screen(ctx.db, ctx.user_id), "Not found"
    routine = await RoutineService(ctx.db).get_routine(ctx.user_id, summary.id)
    today = date.today().isoformat()
    skips = [d for d in (routine.skip_dates or []) if d != today]
    await RoutineService(ctx.db).update_routine(
        ctx.user_id, routine.id, RoutineUpdate(skip_dates=skips)
    )
    return await routine_detail_screen(ctx.db, ctx.user_id, token), "Unskipped"
