"""Interactive Tasks screens (Phase 1 pilot)."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations import telegram_templates as tpl
from app.modules.integrations.telegram import conversation as conv
from app.modules.integrations.telegram import keyboards as kb
from app.modules.integrations.telegram.callbacks import CallbackContext, register
from app.modules.integrations.telegram.ids import resolve_one, short_id
from app.modules.integrations.telegram.navigation import back_home
from app.modules.integrations.telegram.renderer import Screen
from app.modules.tasks.schemas import TaskCreate, TaskUpdate
from app.modules.tasks.service import TaskService

PAGE_SIZE = 5

_STATUS_EMOJI = {
    "pending": "⬜",
    "in_progress": "🔵",
    "completed": "✅",
    "cancelled": "⛔",
}


async def _open_tasks(db: AsyncSession, user_id: str):
    svc = TaskService(db)
    pending = await svc.list_tasks(user_id, status="pending")
    in_prog = await svc.list_tasks(user_id, status="in_progress")
    return list(pending) + list(in_prog)


async def tasks_list_screen(db: AsyncSession, user_id: str, page: int = 0) -> Screen:
    items = await _open_tasks(db, user_id)
    if not items:
        rows = [
            kb.row(kb.button("➕ Add task", "task:add")),
            back_home(refresh="task:list:0"),
        ]
        return Screen(
            text=tpl.join_blocks(tpl._header("Tasks"), "No open tasks. Nice work!"),
            keyboard=kb.inline_keyboard(rows),
        )

    total_pages = max(1, (len(items) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    chunk = items[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]

    lines = []
    rows: list[list[dict]] = []
    for i, t in enumerate(chunk, start=page * PAGE_SIZE + 1):
        emoji = _STATUS_EMOJI.get(t.status, "⬜")
        due = t.due_date.date().isoformat() if t.due_date else "no due"
        sid = short_id(t.id)
        lines.append(f"{i}. {emoji} <b>{tpl.esc(t.title)}</b>\n    <i>{tpl.esc(due)}</i> · <code>{sid}</code>")
        rows.append(
            kb.row(
                kb.button(f"✅ {i}", f"task:done:{sid}"),
                kb.button(f"👁 {i}", f"task:view:{sid}"),
                kb.button(f"📅 {i}", f"task:due:{sid}"),
            )
        )

    if total_pages > 1:
        rows.append(kb.pagination_row(namespace="task", page=page, total_pages=total_pages))
    rows.append(kb.row(kb.button("➕ Add task", "task:add")))
    rows.append(back_home(refresh=f"task:list:{page}"))

    body = "\n\n".join(lines)
    text = tpl.join_blocks(
        tpl._header("Tasks", f"{len(items)} open · page {page + 1}/{total_pages}"),
        body,
    )
    return Screen(text=text, keyboard=kb.inline_keyboard(rows))


async def task_detail_screen(db: AsyncSession, user_id: str, token: str) -> Screen:
    items = await _open_tasks(db, user_id)
    # Also try completed for view
    if not resolve_one(items, token):
        completed = await TaskService(db).list_tasks(user_id, status="completed")
        items = items + list(completed)
    task = resolve_one(items, token)
    if task is None:
        return Screen(
            text=tpl.join_blocks(tpl._header("Not found"), f"No task matching <code>{tpl.esc(token)}</code>."),
            keyboard=kb.inline_keyboard([back_home(back="task:list:0")]),
        )
    sid = short_id(task.id)
    due = task.due_date.date().isoformat() if task.due_date else "no due"
    emoji = _STATUS_EMOJI.get(task.status, "⬜")
    text = tpl.join_blocks(
        tpl._header(task.title, f"{emoji} {task.status}"),
        f"Due: <b>{tpl.esc(due)}</b>\nPriority: {tpl.esc(task.priority)}\n<code>{sid}</code>",
    )
    rows = []
    if task.status in ("pending", "in_progress"):
        rows.append(
            kb.row(
                kb.button("✅ Done", f"task:done:{sid}"),
                kb.button("📅 Due date", f"task:due:{sid}"),
            )
        )
    rows.append(back_home(back="task:list:0", refresh=f"task:view:{sid}"))
    return Screen(text=text, keyboard=kb.inline_keyboard(rows))


@register("task", "list")
async def on_list(ctx: CallbackContext) -> Screen:
    page = int(ctx.args[0]) if ctx.args else 0
    return await tasks_list_screen(ctx.db, ctx.user_id, page)


@register("task", "page")
async def on_page(ctx: CallbackContext) -> Screen:
    page = int(ctx.args[0]) if ctx.args else 0
    return await tasks_list_screen(ctx.db, ctx.user_id, page)


@register("task", "view")
async def on_view(ctx: CallbackContext) -> Screen:
    token = ctx.args[0] if ctx.args else ""
    return await task_detail_screen(ctx.db, ctx.user_id, token)


@register("task", "done")
async def on_done(ctx: CallbackContext) -> tuple[Screen, str]:
    token = ctx.args[0] if ctx.args else ""
    items = await _open_tasks(ctx.db, ctx.user_id)
    task = resolve_one(items, token)
    if task is None:
        return (
            Screen(
                text=tpl.join_blocks(tpl._header("Not found"), "Task already done or missing."),
                keyboard=kb.inline_keyboard([back_home(back="task:list:0")]),
            ),
            "Not found",
        )
    await TaskService(ctx.db).complete_task(ctx.user_id, task.id)
    screen = await tasks_list_screen(ctx.db, ctx.user_id, 0)
    return screen, f"Done: {task.title[:40]}"


@register("task", "due")
async def on_due_menu(ctx: CallbackContext) -> Screen:
    token = ctx.args[0] if ctx.args else ""
    sid = token
    today = date.today()
    rows = [
        kb.row(
            kb.button("Today", f"task:setdue:{sid}:0"),
            kb.button("Tomorrow", f"task:setdue:{sid}:1"),
        ),
        kb.row(
            kb.button("+3 days", f"task:setdue:{sid}:3"),
            kb.button("+1 week", f"task:setdue:{sid}:7"),
        ),
        kb.row(kb.button("⌨ Type date", f"task:duetype:{sid}")),
        back_home(back=f"task:view:{sid}"),
    ]
    return Screen(
        text=tpl.join_blocks(tpl._header("Set due date"), f"Task <code>{tpl.esc(sid)}</code>"),
        keyboard=kb.inline_keyboard(rows),
    )


@register("task", "setdue")
async def on_setdue(ctx: CallbackContext) -> tuple[Screen, str]:
    if len(ctx.args) < 2:
        return await tasks_list_screen(ctx.db, ctx.user_id, 0), "Bad request"
    token, offset_s = ctx.args[0], ctx.args[1]
    try:
        offset = int(offset_s)
    except ValueError:
        offset = 0
    items = await _open_tasks(ctx.db, ctx.user_id)
    task = resolve_one(items, token)
    if task is None:
        return await tasks_list_screen(ctx.db, ctx.user_id, 0), "Not found"
    due = datetime.combine(date.today() + timedelta(days=offset), time(12, 0), tzinfo=timezone.utc)
    await TaskService(ctx.db).update_task(ctx.user_id, task.id, TaskUpdate(due_date=due))
    screen = await task_detail_screen(ctx.db, ctx.user_id, token)
    return screen, f"Due → {due.date().isoformat()}"


@register("task", "duetype")
async def on_due_type(ctx: CallbackContext) -> Screen:
    token = ctx.args[0] if ctx.args else ""
    await conv.begin(
        ctx.db,
        ctx.user_id,
        "task_due",
        "ask_date",
        data={"task_token": token},
        message_id=ctx.message_id,
        chat_id=ctx.chat_id,
    )
    return Screen(
        text=tpl.join_blocks(
            tpl._header("Due date"),
            "Send a date as <code>YYYY-MM-DD</code>, <code>today</code>, or <code>tomorrow</code>.\n"
            "Or /cancel.",
        ),
        keyboard=kb.inline_keyboard([back_home(back=f"task:view:{token}")]),
        edit=True,
    )


@register("task", "add")
async def on_add(ctx: CallbackContext) -> Screen:
    await conv.begin(
        ctx.db,
        ctx.user_id,
        "task_add",
        "ask_title",
        message_id=ctx.message_id,
        chat_id=ctx.chat_id,
    )
    return Screen(
        text=tpl.join_blocks(
            tpl._header("Add task"),
            "Send the task title.\nOr /cancel.",
        ),
        keyboard=kb.inline_keyboard([kb.row(kb.button("❌ Cancel", "task:cancel_add"))]),
    )


@register("task", "cancel_add")
async def on_cancel_add(ctx: CallbackContext) -> Screen:
    conv.cancel(ctx.user_id)
    return await tasks_list_screen(ctx.db, ctx.user_id, 0)


@register("task", "noop")
async def on_noop(ctx: CallbackContext) -> str:
    return ""


# --- Conversation steps ---


@conv.register_step("task_add", "ask_title")
async def step_ask_title(db: AsyncSession, user_id: str, text: str, data: dict) -> Screen:
    title = (text or "").strip()
    if not title:
        return Screen(
            text=tpl.join_blocks(tpl._header("Add task"), "Send the task title."),
            keyboard=kb.inline_keyboard([kb.row(kb.button("❌ Cancel", "task:cancel_add"))]),
        )
    if len(title) > 200:
        return Screen(text="Title too long (max 200). Try again.")
    await conv.advance(user_id, "ask_due", data={"title": title})
    return Screen(
        text=tpl.join_blocks(
            tpl._header("Due date"),
            f"Title: <b>{tpl.esc(title)}</b>\n\n"
            "Tap a due date, or send <code>YYYY-MM-DD</code> / today / tomorrow.",
        ),
        keyboard=kb.inline_keyboard(
            [
                kb.row(
                    kb.button("Today", "task:adddue:0"),
                    kb.button("Tomorrow", "task:adddue:1"),
                ),
                kb.row(kb.button("Skip (today)", "task:adddue:0")),
                kb.row(kb.button("❌ Cancel", "task:cancel_add")),
            ]
        ),
    )


@register("task", "adddue")
async def on_adddue(ctx: CallbackContext) -> tuple[Screen, str]:
    from app.modules.integrations.telegram.state import clear_conversation, get_conversation

    state = get_conversation(ctx.user_id)
    if state is None or state.flow != "task_add":
        return await tasks_list_screen(ctx.db, ctx.user_id, 0), "No active add"
    title = state.data.get("title") or "Untitled"
    offset = int(ctx.args[0]) if ctx.args else 0
    due = datetime.combine(date.today() + timedelta(days=offset), time(12, 0), tzinfo=timezone.utc)
    task = await TaskService(ctx.db).create_task(ctx.user_id, TaskCreate(title=title, due_date=due))
    clear_conversation(ctx.user_id)
    screen = await tasks_list_screen(ctx.db, ctx.user_id, 0)
    return screen, f"Created: {task.title[:40]}"


@conv.register_step("task_add", "ask_due")
async def step_ask_due(db: AsyncSession, user_id: str, text: str, data: dict) -> Screen:
    from app.modules.integrations.telegram.state import clear_conversation

    title = data.get("title") or "Untitled"
    due_dt, err = _parse_due(text)
    if err:
        return Screen(text=f"Could not parse date. Use YYYY-MM-DD, today, or tomorrow.\n({tpl.esc(err)})")
    task = await TaskService(db).create_task(user_id, TaskCreate(title=title, due_date=due_dt))
    clear_conversation(user_id)
    return await tasks_list_screen(db, user_id, 0)


@conv.register_step("task_due", "ask_date")
async def step_due_date(db: AsyncSession, user_id: str, text: str, data: dict) -> Screen:
    from app.modules.integrations.telegram.state import clear_conversation

    token = data.get("task_token") or ""
    due_dt, err = _parse_due(text)
    if err:
        return Screen(text=f"Could not parse date: {tpl.esc(err)}")
    items = await _open_tasks(db, user_id)
    task = resolve_one(items, token)
    if task is None:
        clear_conversation(user_id)
        return await tasks_list_screen(db, user_id, 0)
    await TaskService(db).update_task(user_id, task.id, TaskUpdate(due_date=due_dt))
    clear_conversation(user_id)
    return await task_detail_screen(db, user_id, token)


def _parse_due(raw: str) -> tuple[datetime | None, str | None]:
    token = (raw or "").strip().lower()
    today = date.today()

    def as_due(d: date) -> datetime:
        return datetime.combine(d, time(12, 0), tzinfo=timezone.utc)

    if not token:
        return as_due(today), None
    if token == "today":
        return as_due(today), None
    if token == "tomorrow":
        return as_due(today + timedelta(days=1)), None
    try:
        return as_due(date.fromisoformat(token)), None
    except ValueError:
        return None, token
