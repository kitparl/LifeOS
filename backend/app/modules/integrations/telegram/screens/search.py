"""Universal search screens (Phase 7)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations import telegram_templates as tpl
from app.modules.integrations.telegram import conversation as conv
from app.modules.integrations.telegram import keyboards as kb
from app.modules.integrations.telegram.callbacks import CallbackContext, register
from app.modules.integrations.telegram.navigation import back_home
from app.modules.integrations.telegram.renderer import Screen
from app.modules.integrations.telegram.state import clear_conversation, put_token, get_token
from app.modules.search.service import SearchService

PAGE_SIZE = 5


async def search_results_screen(
    db: AsyncSession, user_id: str, query: str, page: int = 0
) -> Screen:
    resp = await SearchService(db).search(user_id, query, limit=40)
    results = resp.results
    if not results:
        return Screen(
            text=tpl.join_blocks(
                tpl._header("Search"),
                f"No results for <i>{tpl.esc(query)}</i>.",
            ),
            keyboard=kb.inline_keyboard(
                [
                    kb.row(kb.button("🔍 New search", "search:start")),
                    back_home(),
                ]
            ),
        )
    total_pages = max(1, (len(results) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    chunk = results[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]
    lines = []
    for r in chunk:
        sub = f" — {tpl.esc(r.subtitle)}" if r.subtitle else ""
        lines.append(
            f"• <b>{tpl.esc(r.title)}</b>{sub}\n"
            f"  <i>{tpl.esc(r.module)}/{tpl.esc(r.entity_type)}</i>"
        )
    token = put_token({"q": query})
    rows: list[list[dict]] = []
    if total_pages > 1:
        rows.append(
            kb.pagination_row(
                namespace="search", page=page, total_pages=total_pages, extra=token
            )
        )
    rows.append(kb.row(kb.button("🔍 New search", "search:start")))
    rows.append(back_home(refresh=f"search:page:{page}:{token}"))
    text = tpl.join_blocks(
        tpl._header("Search", f"“{query}” · {resp.total} · page {page + 1}/{total_pages}"),
        "\n\n".join(lines),
    )
    return Screen(text=text, keyboard=kb.inline_keyboard(rows))


@register("search", "start")
async def on_start(ctx: CallbackContext) -> Screen:
    await conv.begin(
        ctx.db,
        ctx.user_id,
        "search",
        "ask_query",
        message_id=ctx.message_id,
        chat_id=ctx.chat_id,
    )
    return Screen(
        text=tpl.join_blocks(
            tpl._header("Search"),
            "Send a keyword to search tasks, goals, habits, calendar, and more.\nOr /cancel.",
        ),
        keyboard=kb.inline_keyboard([kb.row(kb.button("❌ Cancel", "nav:home"))]),
    )


@register("search", "page")
async def on_page(ctx: CallbackContext) -> Screen:
    page = int(ctx.args[0]) if ctx.args else 0
    token = ctx.args[1] if len(ctx.args) > 1 else ""
    payload = get_token(token) or {}
    query = payload.get("q") or ""
    if not query:
        return await on_start(ctx)
    return await search_results_screen(ctx.db, ctx.user_id, query, page)


@register("search", "noop")
async def on_noop(ctx: CallbackContext) -> str:
    return ""


@conv.register_step("search", "ask_query")
async def step_query(db: AsyncSession, user_id: str, text: str, data: dict) -> Screen:
    q = (text or "").strip()
    if not q:
        return Screen(text="Send a search keyword.")
    clear_conversation(user_id)
    return await search_results_screen(db, user_id, q, 0)
