"""Dashboard / home screen."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations import telegram_templates as tpl
from app.modules.integrations.telegram import keyboards as kb
from app.modules.integrations.telegram.callbacks import CallbackContext, register
from app.modules.integrations.telegram.navigation import home_keyboard
from app.modules.integrations.telegram.renderer import Screen


async def home_screen(db: AsyncSession, user_id: str) -> Screen:
    text = tpl.join_blocks(
        tpl._header("LifeOS", "Home"),
        "Tap a section below — or use /help for classic commands.",
    )
    return Screen(text=text, keyboard=home_keyboard())


@register("nav", "home")
async def on_home(ctx: CallbackContext) -> Screen:
    return await home_screen(ctx.db, ctx.user_id)


@register("nav", "noop")
async def on_noop(ctx: CallbackContext) -> str:
    return ""
