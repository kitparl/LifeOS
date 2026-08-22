from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.integrations.github_sync_models import (
    SYNC_STATUS_NEVER,
    GitHubSyncState,
)


class GitHubSyncRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_section(self, user_id: str, section_id: str) -> GitHubSyncState | None:
        result = await self.db.execute(
            select(GitHubSyncState).where(
                GitHubSyncState.user_id == user_id,
                GitHubSyncState.section_id == section_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        user_id: str,
        section_id: str,
        md_path: str,
        md_sha: str | None,
        content_hash: str,
        assets_json: str,
        remote_commit_sha: str | None = None,
        sync_status: str = "synced",
        last_error: str | None = None,
    ) -> GitHubSyncState:
        row = await self.get_by_section(user_id, section_id)
        now = datetime.now(timezone.utc)
        if row is None:
            row = GitHubSyncState(
                user_id=user_id,
                section_id=section_id,
                md_path=md_path,
                md_sha=md_sha,
                content_hash=content_hash,
                assets_json=assets_json,
                remote_commit_sha=remote_commit_sha,
                sync_status=sync_status or SYNC_STATUS_NEVER,
                last_error=last_error,
                synced_at=now,
            )
            self.db.add(row)
        else:
            row.md_path = md_path
            row.md_sha = md_sha
            row.content_hash = content_hash
            row.assets_json = assets_json
            if remote_commit_sha is not None:
                row.remote_commit_sha = remote_commit_sha
            row.sync_status = sync_status
            row.last_error = last_error
            row.synced_at = now
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def set_status(
        self,
        user_id: str,
        section_id: str,
        *,
        sync_status: str,
        last_error: str | None = None,
        md_path: str | None = None,
    ) -> GitHubSyncState | None:
        row = await self.get_by_section(user_id, section_id)
        if row is None:
            if md_path is None:
                return None
            row = GitHubSyncState(
                user_id=user_id,
                section_id=section_id,
                md_path=md_path,
                sync_status=sync_status,
                last_error=last_error,
            )
            self.db.add(row)
        else:
            row.sync_status = sync_status
            row.last_error = last_error
        await self.db.flush()
        return row

    async def delete_by_section(self, user_id: str, section_id: str) -> GitHubSyncState | None:
        row = await self.get_by_section(user_id, section_id)
        if row is None:
            return None
        await self.db.delete(row)
        await self.db.flush()
        return row
