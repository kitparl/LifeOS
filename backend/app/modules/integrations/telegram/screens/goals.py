"""Goals interactive screens (Phase 3) — includes linked tasks as Projects substitute."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.goals.schemas import MilestoneUpdate
from app.modules.goals.service import GoalService
from app.modules.integrations import telegram_templates as tpl
from app.modules.integrations.telegram import keyboards as kb
from app.modules.integrations.telegram.callbacks import CallbackContext, register
from app.modules.integrations.telegram.ids import resolve_one, short_id
from app.modules.integrations.telegram.navigation import back_home
from app.modules.integrations.telegram.renderer import Screen
from app.modules.tasks.service import TaskService


async def goals_list_screen(db: AsyncSession, user_id: str) -> Screen:
    goals = await GoalService(db).list_goals(user_id, status="active")
    if not goals:
        return Screen(
            text=tpl.join_blocks(tpl._header("Goals"), "No active goals."),
            keyboard=kb.inline_keyboard([back_home(refresh="goal:list")]),
        )
    lines = []
    rows: list[list[dict]] = []
    for g in goals:
        sid = short_id(g.id)
        lines.append(f"• <b>{tpl.esc(g.title)}</b> · {g.progress}%")
        rows.append(kb.row(kb.button(f"👁 {g.title[:28]}", f"goal:view:{sid}")))
    rows.append(back_home(refresh="goal:list"))
    text = tpl.join_blocks(tpl._header("Goals", f"{len(goals)} active"), "\n".join(lines))
    return Screen(text=text, keyboard=kb.inline_keyboard(rows))


async def goal_detail_screen(db: AsyncSession, user_id: str, token: str) -> Screen:
    goals = await GoalService(db).list_goals(user_id, status="active")
    # Include archived for view
    all_goals = list(goals) + list(await GoalService(db).list_goals(user_id, status="archived"))
    summary = resolve_one(all_goals, token)
    if summary is None:
        return Screen(
            text=tpl.join_blocks(tpl._header("Not found"), "Goal not found."),
            keyboard=kb.inline_keyboard([back_home(back="goal:list")]),
        )
    goal = await GoalService(db).get_goal(user_id, summary.id)
    sid = short_id(goal.id)

    ms_lines = []
    ms_rows: list[list[dict]] = []
    for m in goal.milestones or []:
        check = "✅" if m.completed else "⬜"
        msid = short_id(m.id)
        ms_lines.append(f"{check} {tpl.esc(m.title)}")
        if not m.completed:
            ms_rows.append(kb.row(kb.button(f"✅ {m.title[:28]}", f"goal:msdone:{sid}:{msid}")))

    # Linked tasks (Projects substitute)
    pending, _ = await TaskService(db).list_tasks(user_id, status="pending")
    in_prog, _ = await TaskService(db).list_tasks(user_id, status="in_progress")
    linked = [t for t in list(pending) + list(in_prog) if getattr(t, "goal_id", None) == goal.id]
    task_lines = [f"• {tpl.esc(t.title)}" for t in linked[:10]]

    blocks = [
        tpl._header(goal.title, f"{goal.progress}% · {goal.status}"),
    ]
    if ms_lines:
        blocks.append("<b>Milestones</b>\n" + "\n".join(ms_lines))
    if task_lines:
        blocks.append("<b>Linked tasks</b>\n" + "\n".join(task_lines))
    elif not ms_lines:
        blocks.append("<i>No milestones or linked tasks yet.</i>")

    rows = ms_rows
    rows.append(back_home(back="goal:list", refresh=f"goal:view:{sid}"))
    return Screen(text=tpl.join_blocks(*blocks), keyboard=kb.inline_keyboard(rows))


@register("goal", "list")
async def on_list(ctx: CallbackContext) -> Screen:
    return await goals_list_screen(ctx.db, ctx.user_id)


@register("goal", "view")
async def on_view(ctx: CallbackContext) -> Screen:
    return await goal_detail_screen(ctx.db, ctx.user_id, ctx.args[0] if ctx.args else "")


@register("goal", "msdone")
async def on_msdone(ctx: CallbackContext) -> tuple[Screen, str]:
    if len(ctx.args) < 2:
        return await goals_list_screen(ctx.db, ctx.user_id), "Bad request"
    goal_token, ms_token = ctx.args[0], ctx.args[1]
    goals = await GoalService(ctx.db).list_goals(ctx.user_id, status="active")
    summary = resolve_one(list(goals), goal_token)
    if summary is None:
        return await goals_list_screen(ctx.db, ctx.user_id), "Not found"
    goal = await GoalService(ctx.db).get_goal(ctx.user_id, summary.id)
    milestone = resolve_one(list(goal.milestones or []), ms_token)
    if milestone is None:
        return await goal_detail_screen(ctx.db, ctx.user_id, goal_token), "Milestone not found"
    await GoalService(ctx.db).update_milestone(
        ctx.user_id, goal.id, milestone.id, MilestoneUpdate(completed=True)
    )
    return await goal_detail_screen(ctx.db, ctx.user_id, goal_token), f"Done: {milestone.title[:40]}"
