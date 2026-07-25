"""Analytics card screen (Phase 7)."""

from __future__ import annotations

from app.modules.analytics_dashboard.service import AnalyticsDashboardService
from app.modules.integrations import telegram_templates as tpl
from app.modules.integrations.telegram import keyboards as kb
from app.modules.integrations.telegram.callbacks import CallbackContext, register
from app.modules.integrations.telegram.navigation import back_home
from app.modules.integrations.telegram.renderer import Screen


@register("analytics", "card")
async def on_card(ctx: CallbackContext) -> Screen:
    overview = await AnalyticsDashboardService(ctx.db).overview(ctx.user_id, range_days=30)
    prod = await AnalyticsDashboardService(ctx.db).productivity(ctx.user_id, range_days=30)
    lines = [
        f"Life score: <b>{overview.life_score}</b>",
        f"Tasks today: <b>{overview.todays_tasks}</b>",
        f"Completed (range): <b>{overview.completed_tasks}</b>",
        f"Goal progress: <b>{overview.goal_progress}%</b>",
        f"Habit score: <b>{overview.habit_score}</b>",
        f"Journal streak: <b>{overview.journal_streak}</b>",
        f"Overdue tasks: <b>{prod.overdue_tasks}</b>",
        f"Focus (planned): <b>{prod.focus_hours}h</b>",
    ]
    text = tpl.join_blocks(
        tpl._header("Analytics", f"Last {overview.range_days} days"),
        "\n".join(lines),
        "<i>Open the web dashboard for full charts.</i>",
    )
    return Screen(
        text=text,
        keyboard=kb.inline_keyboard([back_home(refresh="analytics:card")]),
    )
