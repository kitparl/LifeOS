"""Register all interactive screen callback handlers."""

from __future__ import annotations

# Import side-effects: @register decorators
from app.modules.integrations.telegram.screens import (  # noqa: F401
    analytics,
    assignments,
    attachments,
    automations,
    calendar,
    dashboard,
    goals,
    habits,
    notes,
    routines,
    search,
    tasks,
)
