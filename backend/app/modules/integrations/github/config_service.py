"""GitHub connection config: token/repo/branch settings and the access test."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError
from app.core.timezone import utc_now
from app.modules.integrations.github.client import GitHubClient, GitHubClientError, user_facing_github_error
from app.modules.integrations.github.config import mask_config as mask_github_config
from app.modules.integrations.github.config import parse_config as parse_github_config
from app.modules.integrations.github.config import serialize_config as serialize_github_config
from app.modules.integrations.repository import IntegrationRepository
from app.modules.integrations.schemas import (
    GitHubConfigStatus,
    GitHubConfigUpdate,
    GitHubTestResponse,
    IntegrationUpdate,
)


class GitHubConfigService:
    def __init__(self, db: AsyncSession):
        self.repo = IntegrationRepository(db)

    async def get_or_create_github(self, user_id: str):
        return await self.repo.get_or_create(user_id, "github", "GitHub")

    async def get_github_status(self, user_id: str) -> GitHubConfigStatus:
        conn = await self.get_or_create_github(user_id)
        masked = mask_github_config(conn.config_json)
        return GitHubConfigStatus(
            connection_id=conn.id,
            enabled=conn.enabled,
            status=conn.status,
            configured=masked.configured,
            token_masked=masked.token_masked,
            repo=masked.repo,
            branch=masked.branch,
            base_path=masked.base_path,
            notify_github_sync_in_app=masked.notify_github_sync_in_app,
            notify_github_sync_telegram=masked.notify_github_sync_telegram,
            last_sync_at=conn.last_sync_at,
        )

    async def save_github_config(self, user_id: str, data: GitHubConfigUpdate) -> GitHubConfigStatus:
        conn = await self.get_or_create_github(user_id)
        has_secret = data.token is not None
        has_prefs = any(
            v is not None
            for v in (
                data.repo,
                data.branch,
                data.base_path,
                data.notify_github_sync_in_app,
                data.notify_github_sync_telegram,
            )
        )
        if data.enabled is None and not has_secret and not has_prefs:
            raise BadRequestError("No fields to update")

        new_json = serialize_github_config(
            token=data.token,
            repo=data.repo,
            branch=data.branch,
            base_path=data.base_path,
            notify_github_sync_in_app=data.notify_github_sync_in_app,
            notify_github_sync_telegram=data.notify_github_sync_telegram,
            existing_json=conn.config_json,
        )

        update = IntegrationUpdate(config_json=new_json)
        if data.enabled is not None:
            update.enabled = data.enabled
        elif parse_github_config(new_json) is not None:
            update.enabled = True

        updated = await self.repo.update(conn, update)
        if parse_github_config(updated.config_json) is not None and updated.enabled:
            updated.status = "connected"
            await self.repo.db.flush()

        return await self.get_github_status(user_id)

    async def test_github(self, user_id: str) -> GitHubTestResponse:
        conn = await self.repo.get_by_provider(user_id, "github")
        if conn is None:
            return GitHubTestResponse(ok=False, detail="GitHub not connected")
        cfg = parse_github_config(conn.config_json)
        if cfg is None:
            return GitHubTestResponse(ok=False, detail="GitHub not configured")

        client = GitHubClient.from_repo_slug(cfg.token, cfg.repo, branch=cfg.branch)
        try:
            info = await client.validate_access()
            now = utc_now()
            conn.last_sync_at = now
            conn.status = "connected"
            await self.repo.db.flush()
            return GitHubTestResponse(
                ok=True,
                detail=f"Token, repo, branch '{cfg.branch}', and write access verified",
                repo_full_name=str(info.get("full_name") or cfg.repo),
                branch=cfg.branch,
                can_push=True,
            )
        except GitHubClientError as exc:
            conn.status = "error"
            await self.repo.db.flush()
            return GitHubTestResponse(
                ok=False,
                detail=user_facing_github_error(exc),
                repo_full_name=cfg.repo,
                branch=cfg.branch,
                can_push=False,
            )
