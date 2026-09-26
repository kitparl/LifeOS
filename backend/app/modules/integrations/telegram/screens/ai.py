"""AI assistive screens (briefing, task breakdown, natural-language task)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.telegram import conversation as conv
from app.modules.integrations.telegram import keyboards as kb
from app.modules.integrations.telegram import templates as tpl
from app.modules.integrations.telegram.callbacks import CallbackContext, register
from app.modules.integrations.telegram.navigation import back_home
from app.modules.integrations.telegram.renderer import Screen
from app.modules.integrations.telegram.state import clear_conversation


@register("ai", "briefing")
async def on_briefing(ctx: CallbackContext) -> Screen:
    from app.modules.reports.service import ReportsService

    review = await ReportsService(ctx.db).generate_review(ctx.user_id, "daily")
    text = tpl.join_blocks(tpl._header("AI Daily Briefing"), tpl.esc(review.content[:3500]))
    rows = [
        kb.row(
            kb.button("🧩 Break down a task", "ai:breakdown"),
            kb.button("➕ NL add task", "ai:nltask"),
        ),
        back_home(refresh="ai:briefing"),
    ]
    return Screen(text=text, keyboard=kb.inline_keyboard(rows))


@register("ai", "breakdown")
async def on_breakdown_start(ctx: CallbackContext) -> Screen:
    await conv.begin(
        ctx.db,
        ctx.user_id,
        "ai_breakdown",
        "ask_task",
        message_id=ctx.message_id,
        chat_id=ctx.chat_id,
    )
    return Screen(
        text=tpl.join_blocks(
            tpl._header("Task breakdown"),
            "Send the task you want broken into steps.\nOr /cancel.",
        ),
        keyboard=kb.inline_keyboard([kb.row(kb.button("❌ Cancel", "ai:cancel"))]),
    )


@register("ai", "nltask")
async def on_nltask_start(ctx: CallbackContext) -> Screen:
    await conv.begin(
        ctx.db,
        ctx.user_id,
        "ai_nltask",
        "ask_text",
        message_id=ctx.message_id,
        chat_id=ctx.chat_id,
    )
    return Screen(
        text=tpl.join_blocks(
            tpl._header("Natural-language add task"),
            "Describe the task in plain language.\nExample: <i>Remind me to call the dentist next Friday</i>\nOr /cancel.",
        ),
        keyboard=kb.inline_keyboard([kb.row(kb.button("❌ Cancel", "ai:cancel"))]),
    )


@register("ai", "cancel")
async def on_ai_cancel(ctx: CallbackContext) -> Screen:
    clear_conversation(ctx.user_id)
    return await on_briefing(ctx)


@conv.register_step("ai_breakdown", "ask_task")
async def step_breakdown(db: AsyncSession, user_id: str, text: str, data: dict) -> Screen:
    from app.modules.ai.service import AiService

    raw = (text or "").strip()
    if not raw:
        return Screen(text="Send a task description.")
    result = await AiService(db).suggest_task_breakdown(user_id, raw)
    clear_conversation(user_id)
    return Screen(
        text=tpl.join_blocks(tpl._header("Breakdown", raw[:80]), tpl.esc(result[:3500])),
        keyboard=kb.inline_keyboard([back_home(back="ai:briefing")]),
    )


@conv.register_step("ai_nltask", "ask_text")
async def step_nltask(db: AsyncSession, user_id: str, text: str, data: dict) -> Screen:
    from app.modules.ai.service import AiService
    from app.modules.integrations.telegram.screens.tasks import tasks_list_screen

    raw = (text or "").strip()
    if not raw:
        return Screen(text="Describe the task.")
    task = await AiService(db).parse_and_create_task(user_id, raw)
    clear_conversation(user_id)
    if task is None:
        return Screen(
            text=tpl.join_blocks(tpl._header("Could not parse"), "Try a clearer description."),
            keyboard=kb.inline_keyboard([back_home(back="ai:briefing")]),
        )
    due = task.due_date.date().isoformat() if task.due_date else "today"
    screen = await tasks_list_screen(db, user_id, 0)
    screen.text = tpl.join_blocks(
        tpl._header("Task created"),
        f"<b>{tpl.esc(task.title)}</b>\nDue: {tpl.esc(due)}",
    ) + "\n\n" + screen.text
    return screen
