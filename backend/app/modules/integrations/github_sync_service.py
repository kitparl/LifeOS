"""Push Knowledge Notes sections to GitHub (one-way sync, atomic Git Data commits)."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.files.backends import resolve_backend
from app.modules.files.repository import FileRepository
from app.modules.integrations.github_client import (
    GitHubClient,
    GitHubClientError,
    TreeEntry,
    user_facing_github_error,
)
from app.modules.integrations.github_config import DecryptedGitHubConfig, parse_config
from app.modules.integrations.github_slug import slugify
from app.modules.integrations.github_sync_models import (
    SYNC_STATUS_FAILED,
    SYNC_STATUS_SYNCED,
    SYNC_STATUS_SYNCING,
    SYNC_STATUS_UNCHANGED,
)
from app.modules.integrations.github_sync_notifier import notify_github_sync_result
from app.modules.integrations.github_sync_planner import build_sync_plan
from app.modules.integrations.github_sync_repository import GitHubSyncRepository
from app.modules.integrations.repository import IntegrationRepository
from app.modules.knowledge_notes.models import KnowledgeChapter, KnowledgeSection, KnowledgeSubject

logger = logging.getLogger(__name__)

_INLINE_FILE_RE = re.compile(
    r"(!?\[[^\]]*\]\()([^)]*/api/v1/files/([0-9a-f-]{36})/content[^)]*)\)",
    re.IGNORECASE,
)
_SECTION_LOCKS: dict[str, asyncio.Lock] = {}


@dataclass(frozen=True)
class SectionContext:
    section: KnowledgeSection
    chapter: KnowledgeChapter
    subject: KnowledgeSubject


@dataclass(frozen=True)
class AssetRecord:
    file_id: str
    path: str
    sha: str | None = None


def _lock_key(user_id: str, section_id: str) -> str:
    return f"{user_id}:{section_id}"


def _get_lock(user_id: str, section_id: str) -> asyncio.Lock:
    key = _lock_key(user_id, section_id)
    lock = _SECTION_LOCKS.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _SECTION_LOCKS[key] = lock
    return lock


def extract_file_ids(content: str) -> set[str]:
    return {match[2] for match in _INLINE_FILE_RE.findall(content or "")}


def rewrite_markdown(content: str, id_to_relpath: dict[str, str]) -> str:
    if not content or not id_to_relpath:
        return content or ""

    def repl(match: re.Match[str]) -> str:
        prefix = match.group(1)
        file_id = match.group(3)
        relpath = id_to_relpath.get(file_id)
        if not relpath:
            return match.group(0)
        return f"{prefix}{relpath})"

    return _INLINE_FILE_RE.sub(repl, content)


def build_paths(
    subject: KnowledgeSubject,
    chapter: KnowledgeChapter,
    section: KnowledgeSection,
    base_path: str,
) -> tuple[str, str]:
    subject_slug = slugify(subject.title, "subject")
    chapter_slug = slugify(chapter.title, "chapter")
    section_slug = slugify(section.title, "section")
    if not section_slug.endswith(".md"):
        section_slug = f"{section_slug}.md"
    prefix = "/".join(p for p in [base_path.strip("/"), subject_slug, chapter_slug] if p)
    md_path = f"{prefix}/{section_slug}"
    assets_dir = f"{prefix}/assets"
    return md_path, assets_dir


def _asset_filename(record_filename: str, file_id: str) -> str:
    """UUID-prefixed filename to avoid collisions across sections."""
    name = (record_filename or "file").strip()
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name)
    name = name.replace("]", "").replace("[", "") or "file"
    # Keep extension; prefix with full file_id for uniqueness
    return f"{file_id}-{name}"


def _content_hash(md_text: str, asset_checksums: dict[str, str]) -> str:
    payload = md_text + "\n" + json.dumps(asset_checksums, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _parse_assets_json(raw: str | None) -> list[AssetRecord]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    out: list[AssetRecord] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        file_id = str(item.get("file_id") or "")
        path = str(item.get("path") or "")
        sha = item.get("sha")
        if file_id and path:
            out.append(AssetRecord(file_id=file_id, path=path, sha=str(sha) if sha else None))
    return out


def _assets_to_json(assets: list[AssetRecord]) -> str:
    return json.dumps(
        [{"file_id": a.file_id, "path": a.path, "sha": a.sha} for a in assets],
        sort_keys=True,
    )


async def _read_file_bytes(db: AsyncSession, user_id: str, file_id: str) -> tuple[bytes, object]:
    files = FileRepository(db)
    record = await files.get(user_id, file_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"File {file_id} not found")
    backend = resolve_backend(record.storage_backend)
    chunks: list[bytes] = []
    async for chunk in backend.open(record.storage_key):
        chunks.append(chunk)
    return b"".join(chunks), record


def _http_from_github(exc: GitHubClientError) -> HTTPException:
    detail = user_facing_github_error(exc)
    code = status.HTTP_502_BAD_GATEWAY
    if exc.code == "auth":
        code = status.HTTP_401_UNAUTHORIZED
    elif exc.code == "permission":
        code = status.HTTP_403_FORBIDDEN
    elif exc.code == "not_found":
        code = status.HTTP_404_NOT_FOUND
    elif exc.code == "conflict":
        code = status.HTTP_409_CONFLICT
    elif exc.code == "validation":
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    return HTTPException(code, detail=detail)


class GitHubSyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.integrations = IntegrationRepository(db)
        self.sync_repo = GitHubSyncRepository(db)

    async def _load_github_config(self, user_id: str) -> tuple[DecryptedGitHubConfig, object]:
        conn = await self.integrations.get_by_provider(user_id, "github")
        if conn is None or not conn.enabled:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="GitHub integration is not enabled")
        cfg = parse_config(conn.config_json)
        if cfg is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="GitHub is not configured")
        return cfg, conn

    async def _load_section_context(self, user_id: str, section_id: str) -> SectionContext:
        result = await self.db.execute(
            select(KnowledgeSection, KnowledgeChapter, KnowledgeSubject)
            .join(KnowledgeChapter, KnowledgeSection.chapter_id == KnowledgeChapter.id)
            .join(KnowledgeSubject, KnowledgeChapter.subject_id == KnowledgeSubject.id)
            .where(KnowledgeSection.id == section_id, KnowledgeSection.user_id == user_id)
        )
        row = result.first()
        if row is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Section not found")
        section, chapter, subject = row
        return SectionContext(section=section, chapter=chapter, subject=subject)

    def _client(self, cfg: DecryptedGitHubConfig) -> GitHubClient:
        return GitHubClient.from_repo_slug(cfg.token, cfg.repo, branch=cfg.branch)

    async def _apply_plan_atomic(
        self,
        client: GitHubClient,
        message: str,
        plan,
    ) -> tuple[str, dict[str, str]]:
        """Create blobs + one tree/commit. Returns (commit_sha, path→blob_sha)."""
        path_to_sha: dict[str, str] = {}
        entries: list[TreeEntry] = []

        for planned in plan.writable:
            assert planned.content is not None
            blob_sha = await client.create_blob(planned.content)
            path_to_sha[planned.path] = blob_sha
            entries.append(TreeEntry(path=planned.path, sha=blob_sha))

        for planned in plan.deletes:
            entries.append(TreeEntry(path=planned.path, sha=None))

        if not entries:
            return "", path_to_sha

        result = await client.commit_tree_changes(message, entries)
        return result.commit_sha, path_to_sha

    async def sync_section(self, user_id: str, section_id: str) -> dict:
        lock = _get_lock(user_id, section_id)
        if lock.locked():
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Sync already in progress")

        async with lock:
            ctx: SectionContext | None = None
            cfg: DecryptedGitHubConfig | None = None
            md_path = ""
            try:
                cfg, conn = await self._load_github_config(user_id)
                ctx = await self._load_section_context(user_id, section_id)
                client = self._client(cfg)
                md_path, assets_dir = build_paths(ctx.subject, ctx.chapter, ctx.section, cfg.base_path)

                await self.sync_repo.set_status(
                    user_id,
                    section_id,
                    sync_status=SYNC_STATUS_SYNCING,
                    last_error=None,
                    md_path=md_path,
                )

                state = await self.sync_repo.get_by_section(user_id, section_id)
                prev_assets = _parse_assets_json(state.assets_json if state else None)

                file_ids = extract_file_ids(ctx.section.content or "")
                id_to_relpath: dict[str, str] = {}
                asset_checksums: dict[str, str] = {}
                asset_payloads: list[tuple[str, str, bytes]] = []

                for file_id in sorted(file_ids):
                    data, record = await _read_file_bytes(self.db, user_id, file_id)
                    checksum = hashlib.sha256(data).hexdigest()
                    asset_checksums[file_id] = checksum
                    filename = _asset_filename(record.filename, file_id)
                    asset_path = f"{assets_dir}/{filename}"
                    # Relative link from md file sibling assets/
                    id_to_relpath[file_id] = f"./assets/{filename}"
                    asset_payloads.append((file_id, asset_path, data))

                rewritten = rewrite_markdown(ctx.section.content or "", id_to_relpath)
                content_hash = _content_hash(rewritten, asset_checksums)

                plan = build_sync_plan(
                    md_path=md_path,
                    rewritten_md=rewritten,
                    content_hash=content_hash,
                    assets=asset_payloads,
                    previous_md_path=state.md_path if state else None,
                    previous_content_hash=state.content_hash if state else None,
                    previous_assets=[(a.file_id, a.path, a.sha) for a in prev_assets],
                )

                if plan.is_noop:
                    now = datetime.now(timezone.utc)
                    conn.last_sync_at = now
                    await self.sync_repo.upsert(
                        user_id=user_id,
                        section_id=section_id,
                        md_path=md_path,
                        md_sha=state.md_sha if state else None,
                        content_hash=content_hash,
                        assets_json=state.assets_json if state and state.assets_json else "[]",
                        remote_commit_sha=state.remote_commit_sha if state else None,
                        sync_status=SYNC_STATUS_UNCHANGED,
                        last_error=None,
                    )
                    await self.db.flush()
                    return {
                        "status": "unchanged",
                        "message": "Already up to date",
                        "md_path": md_path,
                        "synced_at": now,
                        "remote_commit_sha": state.remote_commit_sha if state else None,
                    }

                commit_msg = f"LifeOS: sync {ctx.section.title}"
                commit_sha, path_to_sha = await self._apply_plan_atomic(client, commit_msg, plan)

                uploaded_assets: list[AssetRecord] = []
                for file_id, path, _ in asset_payloads:
                    uploaded_assets.append(
                        AssetRecord(file_id=file_id, path=path, sha=path_to_sha.get(path))
                    )

                md_sha = path_to_sha.get(md_path) or (state.md_sha if state else None)
                now = datetime.now(timezone.utc)
                await self.sync_repo.upsert(
                    user_id=user_id,
                    section_id=section_id,
                    md_path=md_path,
                    md_sha=md_sha,
                    content_hash=content_hash,
                    assets_json=_assets_to_json(uploaded_assets),
                    remote_commit_sha=commit_sha or None,
                    sync_status=SYNC_STATUS_SYNCED,
                    last_error=None,
                )
                conn.last_sync_at = now
                conn.status = "connected"
                await self.db.flush()

                result = {
                    "status": "synced",
                    "message": f"Pushed to {cfg.repo}:{cfg.branch}/{md_path}",
                    "md_path": md_path,
                    "synced_at": now,
                    "remote_commit_sha": commit_sha or None,
                }
                await notify_github_sync_result(
                    self.db,
                    user_id=user_id,
                    section_id=section_id,
                    subject_id=ctx.subject.id,
                    section_title=ctx.section.title,
                    status="synced",
                    message=result["message"],
                    repo=cfg.repo,
                )
                return result
            except GitHubClientError as exc:
                detail = user_facing_github_error(exc)
                if ctx is not None:
                    await self.sync_repo.set_status(
                        user_id,
                        section_id,
                        sync_status=SYNC_STATUS_FAILED,
                        last_error=detail,
                        md_path=md_path or None,
                    )
                    await notify_github_sync_result(
                        self.db,
                        user_id=user_id,
                        section_id=section_id,
                        subject_id=ctx.subject.id,
                        section_title=ctx.section.title,
                        status="failed",
                        message=detail,
                        repo=cfg.repo if cfg else None,
                    )
                raise _http_from_github(exc) from exc
            except HTTPException as exc:
                if ctx is not None and exc.status_code != status.HTTP_409_CONFLICT:
                    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
                    await self.sync_repo.set_status(
                        user_id,
                        section_id,
                        sync_status=SYNC_STATUS_FAILED,
                        last_error=detail,
                        md_path=md_path or None,
                    )
                    await notify_github_sync_result(
                        self.db,
                        user_id=user_id,
                        section_id=section_id,
                        subject_id=ctx.subject.id,
                        section_title=ctx.section.title,
                        status="failed",
                        message=detail,
                        repo=cfg.repo if cfg else None,
                    )
                raise
            except Exception as exc:
                detail = str(exc) or "Sync failed"
                if ctx is not None:
                    await self.sync_repo.set_status(
                        user_id,
                        section_id,
                        sync_status=SYNC_STATUS_FAILED,
                        last_error=detail,
                        md_path=md_path or None,
                    )
                    await notify_github_sync_result(
                        self.db,
                        user_id=user_id,
                        section_id=section_id,
                        subject_id=ctx.subject.id,
                        section_title=ctx.section.title,
                        status="failed",
                        message=detail,
                        repo=cfg.repo if cfg else None,
                    )
                raise

    async def delete_section_remote(self, user_id: str, section_id: str) -> None:
        state = await self.sync_repo.get_by_section(user_id, section_id)
        if state is None:
            return
        conn = await self.integrations.get_by_provider(user_id, "github")
        cfg = parse_config(conn.config_json) if conn else None
        if cfg is None:
            await self.sync_repo.delete_by_section(user_id, section_id)
            return
        try:
            client = self._client(cfg)
            entries: list[TreeEntry] = [TreeEntry(path=state.md_path, sha=None)]
            for asset in _parse_assets_json(state.assets_json):
                entries.append(TreeEntry(path=asset.path, sha=None))
            await client.commit_tree_changes(
                f"LifeOS: delete section {section_id}",
                entries,
            )
        except Exception:
            logger.exception("GitHub remote delete failed for section=%s", section_id)
        await self.sync_repo.delete_by_section(user_id, section_id)
