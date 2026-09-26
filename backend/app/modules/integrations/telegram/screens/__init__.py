"""Register all interactive screen callback handlers."""

from __future__ import annotations

# Import side-effects: @register decorators
from app.modules.integrations.telegram.screens import (  # noqa: F401
    ai,
    analytics,
    assignments,
    attachments,
    calendar,
    dashboard,
    habits,
    notes,
    routines,
    search,
    tasks,
)
