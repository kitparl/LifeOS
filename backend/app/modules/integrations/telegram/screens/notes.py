"""Notes quick capture via knowledge_notes Inbox (Phase 4b)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations import telegram_templates as tpl
from app.modules.integrations.telegram import conversation as conv
from app.modules.integrations.telegram import keyboards as kb
from app.modules.integrations.telegram.callbacks import CallbackContext, register
from app.modules.integrations.telegram.navigation import back_home
from app.modules.integrations.telegram.renderer import Screen
from app.modules.integrations.telegram.state import clear_conversation
from app.modules.knowledge_notes.schemas import ChapterCreate, SectionCreate, SubjectCreate
from app.modules.knowledge_notes.service import KnowledgeNotesService

INBOX_SUBJECT = "Telegram Inbox"
INBOX_CHAPTER = "Quick Capture"


async def _ensure_inbox(db: AsyncSession, user_id: str) -> str:
    """Return chapter_id for Telegram Inbox / Quick Capture, creating if needed."""
    svc = KnowledgeNotesService(db)
    subjects = await svc.list_subjects(user_id)
    subject = next((s for s in subjects if s.title == INBOX_SUBJECT), None)
    if subject is None:
        detail = await svc.create_subject(
            user_id, SubjectCreate(title=INBOX_SUBJECT, description="Captured from Telegram", icon="📝")
        )
        subject_id = detail.id
        chapter = await svc.create_chapter(user_id, subject_id, ChapterCreate(title=INBOX_CHAPTER))
        return chapter.id

    detail = await svc.get_subject(user_id, subject.id)
    for ch in detail.chapters or []:
        if ch.title == INBOX_CHAPTER:
            return ch.id
    chapter = await svc.create_chapter(user_id, subject.id, ChapterCreate(title=INBOX_CHAPTER))
    return chapter.id


async def notes_menu_screen(db: AsyncSession, user_id: str) -> Screen:
    text = tpl.join_blocks(
        tpl._header("Notes"),
        "Quick capture saves into <b>Telegram Inbox → Quick Capture</b>.",
    )
    rows = [
        kb.row(kb.button("➕ Capture note", "note:capture")),
        kb.row(kb.button("🔍 Search notes", "note:search")),
        kb.row(kb.button("📚 Subjects", "note:subjects")),
        back_home(refresh="note:menu"),
    ]
    return Screen(text=text, keyboard=kb.inline_keyboard(rows))


async def subjects_screen(db: AsyncSession, user_id: str) -> Screen:
    subjects = await KnowledgeNotesService(db).list_subjects(user_id)
    if not subjects:
        lines = ["No subjects yet. Capture a note to create the Inbox."]
    else:
        lines = [
            f"• <b>{tpl.esc(s.title)}</b> · {s.section_count} sections"
            for s in subjects[:20]
        ]
    return Screen(
        text=tpl.join_blocks(tpl._header("Subjects"), "\n".join(lines)),
        keyboard=kb.inline_keyboard([back_home(back="note:menu", refresh="note:subjects")]),
    )


@register("note", "menu")
async def on_menu(ctx: CallbackContext) -> Screen:
    return await notes_menu_screen(ctx.db, ctx.user_id)


@register("note", "subjects")
async def on_subjects(ctx: CallbackContext) -> Screen:
    return await subjects_screen(ctx.db, ctx.user_id)


@register("note", "capture")
async def on_capture(ctx: CallbackContext) -> Screen:
    await conv.begin(
        ctx.db,
        ctx.user_id,
        "note_capture",
        "ask_text",
        message_id=ctx.message_id,
        chat_id=ctx.chat_id,
    )
    return Screen(
        text=tpl.join_blocks(
            tpl._header("Quick capture"),
            "Send your note as plain text.\nFirst line becomes the title.\nOr /cancel.",
        ),
        keyboard=kb.inline_keyboard([kb.row(kb.button("❌ Cancel", "note:cancel"))]),
    )


@register("note", "cancel")
async def on_cancel(ctx: CallbackContext) -> Screen:
    clear_conversation(ctx.user_id)
    return await notes_menu_screen(ctx.db, ctx.user_id)


@register("note", "search")
async def on_search_start(ctx: CallbackContext) -> Screen:
    await conv.begin(
        ctx.db,
        ctx.user_id,
        "note_search",
        "ask_query",
        message_id=ctx.message_id,
        chat_id=ctx.chat_id,
    )
    return Screen(
        text=tpl.join_blocks(tpl._header("Search notes"), "Send a keyword.\nOr /cancel."),
        keyboard=kb.inline_keyboard([kb.row(kb.button("❌ Cancel", "note:cancel"))]),
    )


@conv.register_step("note_capture", "ask_text")
async def step_capture(db: AsyncSession, user_id: str, text: str, data: dict) -> Screen:
    raw = (text or "").strip()
    if not raw:
        return Screen(text="Send some text for the note.")
    lines = raw.splitlines()
    title = lines[0][:200]
    content = "\n".join(lines[1:]).strip() if len(lines) > 1 else raw
    chapter_id = await _ensure_inbox(db, user_id)
    section = await KnowledgeNotesService(db).create_section(
        user_id, chapter_id, SectionCreate(title=title, content=content)
    )
    clear_conversation(user_id)
    return Screen(
        text=tpl.join_blocks(
            tpl._header("Note saved"),
            f"<b>{tpl.esc(section.title)}</b>\nSaved to Telegram Inbox.",
        ),
        keyboard=kb.inline_keyboard(
            [
                kb.row(kb.button("➕ Another", "note:capture")),
                back_home(back="note:menu"),
            ]
        ),
    )


@conv.register_step("note_search", "ask_query")
async def step_search(db: AsyncSession, user_id: str, text: str, data: dict) -> Screen:
    q = (text or "").strip()
    if not q:
        return Screen(text="Send a keyword to search.")
    hits = await KnowledgeNotesService(db).search(user_id, q)
    clear_conversation(user_id)
    if not hits:
        return Screen(
            text=tpl.join_blocks(tpl._header("Search"), f"No results for <i>{tpl.esc(q)}</i>."),
            keyboard=kb.inline_keyboard([back_home(back="note:menu")]),
        )
    lines = [
        f"• <b>{tpl.esc(h.section_title)}</b>\n  <i>{tpl.esc(h.subject_title)} / {tpl.esc(h.chapter_title)}</i>\n  {tpl.esc(h.snippet[:120])}"
        for h in hits[:10]
    ]
    return Screen(
        text=tpl.join_blocks(tpl._header("Search", f"{len(hits)} hits"), "\n\n".join(lines)),
        keyboard=kb.inline_keyboard([back_home(back="note:menu", refresh="note:search")]),
    )
