"""Telegram Accept/Reject assignment callbacks — API only, no business logic here."""

from __future__ import annotations

from sqlalchemy import select

from app.modules.integrations import telegram_templates as tpl
from app.modules.integrations.telegram import keyboards as kb
from app.modules.integrations.telegram.callbacks import CallbackContext, register
from app.modules.integrations.telegram.navigation import back_home
from app.modules.integrations.telegram.renderer import Screen
from app.modules.tasks.assignment_service import AssignmentService, load_task_for_actor
from app.modules.tasks.models import Task, TaskAssignment


async def _resolve_task_and_assignment(ctx: CallbackContext):
    if len(ctx.args) < 2:
        return None, None, "Missing task/assignment id"
    task_token, asg_token = ctx.args[0], ctx.args[1]
    # Find task by prefix among tasks assigned to this user
    result = await ctx.db.execute(
        select(Task)
        .join(TaskAssignment, TaskAssignment.task_id == Task.id)
        .where(
            Task.deleted_at.is_(None),
            TaskAssignment.assignee_user_id == ctx.user_id,
            TaskAssignment.status == "pending",
            Task.id.startswith(task_token),
        )
    )
    task = result.scalars().first()
    if task is None:
        # Fallback: any accessible task matching prefix
        result = await ctx.db.execute(
            select(Task).where(Task.deleted_at.is_(None), Task.id.startswith(task_token))
        )
        task = result.scalars().first()
    if task is None:
        return None, None, "Task not found"
    asg_result = await ctx.db.execute(
        select(TaskAssignment).where(
            TaskAssignment.task_id == task.id,
            TaskAssignment.id.startswith(asg_token),
        )
    )
    assignment = asg_result.scalars().first()
    if assignment is None:
        return task, None, "Assignment not found"
    return task, assignment, None


@register("asg", "accept")
async def on_accept(ctx: CallbackContext) -> tuple[Screen, str]:
    task, assignment, err = await _resolve_task_and_assignment(ctx)
    if err or task is None or assignment is None:
        return (
            Screen(
                text=tpl.join_blocks(tpl._header("Assignment"), tpl.esc(err or "Not found")),
                keyboard=kb.inline_keyboard([back_home()]),
            ),
            err or "Not found",
        )
    try:
        task = await load_task_for_actor(ctx.db, task.id, ctx.user_id)
        await AssignmentService(ctx.db).accept(task, assignment.id, ctx.user_id)
    except Exception as exc:
        return (
            Screen(
                text=tpl.join_blocks(tpl._header("Assignment"), tpl.esc(str(exc.detail if hasattr(exc, "detail") else exc))),
                keyboard=kb.inline_keyboard([back_home()]),
            ),
            "Failed",
        )
    return (
        Screen(
            text=tpl.join_blocks(tpl._header("Accepted"), f"<b>{tpl.esc(task.title)}</b>"),
            keyboard=kb.inline_keyboard([back_home()]),
        ),
        f"Accepted: {task.title[:40]}",
    )


@register("asg", "reject")
async def on_reject(ctx: CallbackContext) -> tuple[Screen, str]:
    task, assignment, err = await _resolve_task_and_assignment(ctx)
    if err or task is None or assignment is None:
        return (
            Screen(
                text=tpl.join_blocks(tpl._header("Assignment"), tpl.esc(err or "Not found")),
                keyboard=kb.inline_keyboard([back_home()]),
            ),
            err or "Not found",
        )
    try:
        task = await load_task_for_actor(ctx.db, task.id, ctx.user_id)
        await AssignmentService(ctx.db).reject(task, assignment.id, ctx.user_id)
    except Exception as exc:
        return (
            Screen(
                text=tpl.join_blocks(tpl._header("Assignment"), tpl.esc(str(getattr(exc, "detail", exc)))),
                keyboard=kb.inline_keyboard([back_home()]),
            ),
            "Failed",
        )
    return (
        Screen(
            text=tpl.join_blocks(tpl._header("Rejected"), f"<b>{tpl.esc(task.title)}</b> returned to owner."),
            keyboard=kb.inline_keyboard([back_home()]),
        ),
        f"Rejected: {task.title[:40]}",
    )
