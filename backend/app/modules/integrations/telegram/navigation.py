"""Navigation helpers and shared screen footer conventions."""

from __future__ import annotations

from app.modules.integrations.telegram import keyboards as kb


def home_keyboard() -> dict:
    """Dashboard quick-nav buttons."""
    return kb.inline_keyboard(
        [
            kb.row(kb.button("📋 Tasks", "task:list:0"), kb.button("📅 Today", "cal:today")),
            kb.row(kb.button("🔁 Habits", "habit:list"), kb.button("🎯 Goals", "goal:list")),
            kb.row(kb.button("🗓 Calendar", "cal:week"), kb.button("⏱ Routines", "routine:list")),
            kb.row(kb.button("📝 Notes", "note:menu"), kb.button("⚙️ Automations", "auto:list")),
            kb.row(kb.button("📊 Analytics", "analytics:card"), kb.button("🔍 Search", "search:start")),
            kb.row(kb.button("🤖 AI Briefing", "ai:briefing")),
        ]
    )


def back_home(*, back: str | None = None, refresh: str | None = None) -> list:
    return kb.nav_row(back=back, home=True, refresh=refresh)
