"""Telegram interactive UI kernel — presentation only, no business logic."""

from __future__ import annotations

from app.modules.integrations.telegram.renderer import Screen, render_screen
from app.modules.integrations.telegram.update_router import route_update

__all__ = ["Screen", "render_screen", "route_update"]
