"""In-app and Telegram notifications for GitHub Knowledge Notes sync."""

from __future__ import annotations

import html
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.github_config import parse_preferences
from app.modules.integrations.outbox_repository import OutboxRepository
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.telegram_config import parse_config as parse_telegram_config
from app.modules.notifications.schemas import NotificationCreate
from app.modules.notifications.service import NotificationService

logger = logging.getLogger(__name__)


async def notify_github_sync_result(
    db: AsyncSession,
    *,
    user_id: str,
    section_id: str,
    subject_id: str,
    section_title: str,
    status: str,
    message: str,
    repo: str | None = None,
) -> None:
    """Notify on synced/failed GitHub section sync. Skips unchanged; respects per-channel toggles."""
    if status == "unchanged":
        return

    gh_conn = await IntegrationRepository(db).get_by_provider(user_id, "github")
    if gh_conn is None:
        return
    prefs = parse_preferences(gh_conn.config_json)
    if not prefs.notify_github_sync_in_app and not prefs.notify_github_sync_telegram:
        return

    title = section_title or "Section"
    route = f"/knowledge/{subject_id}?section={section_id}"

    if status == "synced":
        repo_bit = f" ({repo})" if repo else ""
        in_app = f'Pushed "{title}" to GitHub{repo_bit}'
        telegram = f"GitHub sync: pushed <b>{html.escape(title)}</b>{html.escape(repo_bit)}"
    else:
        detail = message or "Sync failed"
        in_app = f'GitHub sync failed for "{title}": {detail}'
        telegram = f"GitHub sync failed for <b>{html.escape(title)}</b>: {html.escape(detail)}"

    if prefs.notify_github_sync_in_app:
        try:
            await NotificationService(db).create(
                user_id,
                NotificationCreate(
                    message=in_app,
                    module="knowledge_notes",
                    entity_id=section_id,
                    route=route,
                ),
            )
        except Exception:
            logger.exception("In-app GitHub sync notification failed section=%s", section_id)

    if not prefs.notify_github_sync_telegram:
        return

    tg_conn = await IntegrationRepository(db).get_by_provider(user_id, "telegram")
    if tg_conn is None or not tg_conn.enabled or parse_telegram_config(tg_conn.config_json) is None:
        return

    try:
        await OutboxRepository(db).enqueue(user_id, telegram, channel="telegram", parse_mode="HTML")
        db.info["outbox_enqueued"] = True
    except Exception:
        logger.exception("Telegram GitHub sync notification enqueue failed section=%s", section_id)
