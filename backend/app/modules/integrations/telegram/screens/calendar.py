"""Calendar interactive screens (Phase 2)."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.calendar.service import CalendarService
from app.modules.integrations import telegram_templates as tpl
from app.modules.integrations.telegram import keyboards as kb
from app.modules.integrations.telegram.callbacks import CallbackContext, register
from app.modules.integrations.telegram.ids import resolve_one, short_id
from app.modules.integrations.telegram.navigation import back_home
from app.modules.integrations.telegram.renderer import Screen


def _day_bounds(d: date) -> tuple[datetime, datetime]:
    start = datetime.combine(d, time.min, tzinfo=timezone.utc)
    end = datetime.combine(d, time.max, tzinfo=timezone.utc)
    return start, end


async def today_screen(db: AsyncSession, user_id: str) -> Screen:
    today = date.today()
    start, end = _day_bounds(today)
    events = await CalendarService(db).list_events(user_id, start=start, end=end)
    if not events:
        text = tpl.join_blocks(tpl._header("Today", today.isoformat()), "Nothing on the calendar.")
        rows = [
            kb.row(kb.button("Week view", "cal:week")),
            back_home(refresh="cal:today"),
        ]
        return Screen(text=text, keyboard=kb.inline_keyboard(rows))

    lines = []
    rows: list[list[dict]] = []
    for e in events[:15]:
        when = e.starts_at.strftime("%H:%M") if e.starts_at else "?"
        sid = short_id(e.id)
        lines.append(f"• <b>{tpl.esc(when)}</b> {tpl.esc(e.title)}")
        rows.append(kb.row(kb.button(f"👁 {e.title[:24]}", f"cal:view:{sid}")))
    rows.append(kb.row(kb.button("Week view", "cal:week")))
    rows.append(back_home(refresh="cal:today"))
    text = tpl.join_blocks(
        tpl._header("Today", f"{today.isoformat()} · {len(events)} events"),
        "\n".join(lines),
    )
    return Screen(text=text, keyboard=kb.inline_keyboard(rows))


async def week_screen(db: AsyncSession, user_id: str) -> Screen:
    today = date.today()
    start = datetime.combine(today, time.min, tzinfo=timezone.utc)
    end = datetime.combine(today + timedelta(days=7), time.max, tzinfo=timezone.utc)
    events = await CalendarService(db).list_events(user_id, start=start, end=end)
    if not events:
        text = tpl.join_blocks(tpl._header("This week"), "No upcoming events.")
        return Screen(
            text=text,
            keyboard=kb.inline_keyboard(
                [kb.row(kb.button("Today", "cal:today")), back_home(refresh="cal:week")]
            ),
        )

    lines = []
    rows: list[list[dict]] = []
    for e in events[:20]:
        when = e.starts_at.strftime("%a %d %H:%M") if e.starts_at else "?"
        sid = short_id(e.id)
        lines.append(f"• <b>{tpl.esc(when)}</b> {tpl.esc(e.title)}")
        rows.append(kb.row(kb.button(f"👁 {e.title[:24]}", f"cal:view:{sid}")))
    rows.append(kb.row(kb.button("Today", "cal:today")))
    rows.append(back_home(refresh="cal:week"))
    text = tpl.join_blocks(
        tpl._header("This week", f"{len(events)} events"),
        "\n".join(lines),
    )
    return Screen(text=text, keyboard=kb.inline_keyboard(rows))


async def event_detail_screen(db: AsyncSession, user_id: str, token: str) -> Screen:
    today = date.today()
    start = datetime.combine(today - timedelta(days=1), time.min, tzinfo=timezone.utc)
    end = datetime.combine(today + timedelta(days=30), time.max, tzinfo=timezone.utc)
    events = await CalendarService(db).list_events(user_id, start=start, end=end)
    summary = resolve_one(list(events), token)
    if summary is None:
        return Screen(
            text=tpl.join_blocks(tpl._header("Not found"), "Event not found."),
            keyboard=kb.inline_keyboard([back_home(back="cal:today")]),
        )
    try:
        event = await CalendarService(db).get_event(user_id, summary.id)
    except Exception:
        event = summary
    when = event.starts_at.strftime("%Y-%m-%d %H:%M") if event.starts_at else "?"
    ends = event.ends_at.strftime("%H:%M") if getattr(event, "ends_at", None) else ""
    loc = getattr(event, "location", None) or ""
    desc = getattr(event, "description", None) or ""
    parts = [f"When: <b>{tpl.esc(when)}</b>" + (f"–{tpl.esc(ends)}" if ends else "")]
    if loc:
        parts.append(f"Location: {tpl.esc(loc)}")
    if desc:
        parts.append(tpl.esc(desc[:400]))
    text = tpl.join_blocks(tpl._header(event.title), "\n".join(parts))
    return Screen(
        text=text,
        keyboard=kb.inline_keyboard([back_home(back="cal:today", refresh=f"cal:view:{token}")]),
    )


@register("cal", "today")
async def on_today(ctx: CallbackContext) -> Screen:
    return await today_screen(ctx.db, ctx.user_id)


@register("cal", "week")
async def on_week(ctx: CallbackContext) -> Screen:
    return await week_screen(ctx.db, ctx.user_id)


@register("cal", "view")
async def on_view(ctx: CallbackContext) -> Screen:
    return await event_detail_screen(ctx.db, ctx.user_id, ctx.args[0] if ctx.args else "")
