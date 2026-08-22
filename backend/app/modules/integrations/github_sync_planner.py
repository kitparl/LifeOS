"""Plan Knowledge Notes → GitHub file operations before committing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

PlanAction = Literal["create", "update", "delete", "unchanged"]


@dataclass(frozen=True)
class PlannedFile:
    action: PlanAction
    path: str
    content: bytes | None = None
    previous_sha: str | None = None


@dataclass
class SyncPlan:
    md_path: str
    content_hash: str
    rewritten_md: str
    assets: list[tuple[str, str, bytes]]  # (file_id, path, content)
    files: list[PlannedFile] = field(default_factory=list)
    deletes: list[PlannedFile] = field(default_factory=list)

    @property
    def is_noop(self) -> bool:
        return not any(f.action in ("create", "update", "delete") for f in self.files + self.deletes)

    @property
    def writable(self) -> list[PlannedFile]:
        return [f for f in self.files if f.action in ("create", "update") and f.content is not None]


def build_sync_plan(
    *,
    md_path: str,
    rewritten_md: str,
    content_hash: str,
    assets: list[tuple[str, str, bytes]],
    previous_md_path: str | None,
    previous_content_hash: str | None,
    previous_assets: list[tuple[str, str, str | None]],  # file_id, path, sha
) -> SyncPlan:
    """Build create/update/delete plan. Only LifeOS-tracked previous paths may be deleted."""
    plan = SyncPlan(
        md_path=md_path,
        content_hash=content_hash,
        rewritten_md=rewritten_md,
        assets=assets,
    )

    prev_by_id = {fid: (path, sha) for fid, path, sha in previous_assets}
    desired_paths = {path for _, path, _ in assets} | {md_path}

    # Markdown
    if previous_md_path and previous_md_path != md_path:
        plan.deletes.append(
            PlannedFile(action="delete", path=previous_md_path, previous_sha=None)
        )
        plan.files.append(
            PlannedFile(
                action="create",
                path=md_path,
                content=rewritten_md.encode("utf-8"),
            )
        )
    elif previous_content_hash == content_hash and previous_md_path == md_path:
        plan.files.append(PlannedFile(action="unchanged", path=md_path))
    elif previous_md_path == md_path:
        plan.files.append(
            PlannedFile(
                action="update",
                path=md_path,
                content=rewritten_md.encode("utf-8"),
            )
        )
    else:
        plan.files.append(
            PlannedFile(
                action="create",
                path=md_path,
                content=rewritten_md.encode("utf-8"),
            )
        )

    # Assets
    for file_id, path, content in assets:
        prev = prev_by_id.get(file_id)
        if prev is None:
            plan.files.append(PlannedFile(action="create", path=path, content=content))
        elif prev[0] != path:
            plan.deletes.append(PlannedFile(action="delete", path=prev[0], previous_sha=prev[1]))
            plan.files.append(PlannedFile(action="create", path=path, content=content))
        else:
            # Path same — content may have changed; treat as update (hash covers overall noop)
            if previous_content_hash == content_hash and previous_md_path == md_path:
                plan.files.append(PlannedFile(action="unchanged", path=path, previous_sha=prev[1]))
            else:
                plan.files.append(
                    PlannedFile(action="update", path=path, content=content, previous_sha=prev[1])
                )

    # Orphan assets (tracked before, not desired now)
    for file_id, path, sha in previous_assets:
        if path not in desired_paths and path != previous_md_path:
            plan.deletes.append(PlannedFile(action="delete", path=path, previous_sha=sha))

    # If overall hash matches and path unchanged, force noop (ignore per-file noise)
    if previous_content_hash == content_hash and previous_md_path == md_path:
        plan.files = [PlannedFile(action="unchanged", path=md_path)]
        for _, path, _ in assets:
            plan.files.append(PlannedFile(action="unchanged", path=path))
        plan.deletes = []

    return plan
