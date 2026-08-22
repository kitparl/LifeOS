"""Encrypt/decrypt and mask GitHub integration config stored in config_json."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from app.core.crypto import decrypt, encrypt

logger = logging.getLogger(__name__)

DEFAULT_BRANCH = "main"
# Empty = repo root (subjects like python/ at top level, no wrapper folder).
DEFAULT_BASE_PATH = ""
_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class DecryptedGitHubConfig:
    token: str
    repo: str
    branch: str
    base_path: str


@dataclass(frozen=True)
class GitHubPreferences:
    notify_github_sync_in_app: bool = False
    notify_github_sync_telegram: bool = False


@dataclass(frozen=True)
class MaskedGitHubConfig:
    configured: bool
    token_masked: str | None
    repo: str | None
    branch: str
    base_path: str
    notify_github_sync_in_app: bool = False
    notify_github_sync_telegram: bool = False


def parse_preferences(config_json: str | None) -> GitHubPreferences:
    data = _load_json(config_json)
    # Legacy single toggle → both channels when new keys are absent.
    legacy = data.get("notify_github_sync")
    if "notify_github_sync_in_app" in data:
        in_app = bool(data["notify_github_sync_in_app"])
    else:
        in_app = bool(legacy) if legacy is not None else False
    if "notify_github_sync_telegram" in data:
        telegram = bool(data["notify_github_sync_telegram"])
    else:
        telegram = bool(legacy) if legacy is not None else False
    return GitHubPreferences(
        notify_github_sync_in_app=in_app,
        notify_github_sync_telegram=telegram,
    )


def _mask_token(token: str) -> str:
    if not token:
        return ""
    if len(token) <= 4:
        return "****"
    return f"****{token[-4:]}"


def _load_json(config_json: str | None) -> dict[str, Any]:
    if not config_json:
        return {}
    try:
        parsed = json.loads(config_json)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _normalize_repo(raw: str | None) -> str:
    value = (raw or "").strip()
    if not value or not _REPO_RE.match(value):
        return ""
    return value


def _normalize_branch(raw: str | None, default: str = DEFAULT_BRANCH) -> str:
    value = (raw or default).strip() or default
    return value.replace("/", "").replace("\\", "") or default


def _normalize_base_path(raw: str | None, default: str = DEFAULT_BASE_PATH) -> str:
    """Normalize base path. Empty string means repo root (no wrapper folder)."""
    if raw is None:
        return default
    value = raw.strip().strip("/\\")
    if not value:
        return ""
    parts = [p for p in value.replace("\\", "/").split("/") if p and p not in (".", "..")]
    return "/".join(parts)


def serialize_config(
    *,
    token: str | None = None,
    repo: str | None = None,
    branch: str | None = None,
    base_path: str | None = None,
    notify_github_sync_in_app: bool | None = None,
    notify_github_sync_telegram: bool | None = None,
    existing_json: str | None = None,
) -> str:
    existing = _load_json(existing_json)
    token_enc = existing.get("token_enc") or existing.get("pat_enc") or ""

    if not token_enc and existing.get("token"):
        token_enc = encrypt(str(existing["token"]))

    if token is not None and token.strip():
        token_enc = encrypt(token.strip())

    current = parse_config(existing_json)
    resolved_repo = _normalize_repo(repo) if repo is not None else (current.repo if current else "")
    resolved_branch = (
        _normalize_branch(branch) if branch is not None else (current.branch if current else DEFAULT_BRANCH)
    )
    resolved_base = (
        _normalize_base_path(base_path)
        if base_path is not None
        else (current.base_path if current else DEFAULT_BASE_PATH)
    )
    prefs = parse_preferences(existing_json)

    payload: dict[str, Any] = {
        "token_enc": token_enc or "",
        "repo": resolved_repo,
        "branch": resolved_branch,
        "base_path": resolved_base,
        "notify_github_sync_in_app": (
            bool(notify_github_sync_in_app)
            if notify_github_sync_in_app is not None
            else prefs.notify_github_sync_in_app
        ),
        "notify_github_sync_telegram": (
            bool(notify_github_sync_telegram)
            if notify_github_sync_telegram is not None
            else prefs.notify_github_sync_telegram
        ),
    }
    return json.dumps(payload)


def parse_config(config_json: str | None) -> DecryptedGitHubConfig | None:
    data = _load_json(config_json)
    if not data:
        if config_json:
            logger.warning("Invalid github config_json (not JSON)")
        return None

    token = ""
    try:
        if data.get("token_enc"):
            token = decrypt(str(data["token_enc"]))
        elif data.get("pat_enc"):
            token = decrypt(str(data["pat_enc"]))
        elif data.get("token"):
            token = str(data["token"])
    except ValueError:
        logger.warning("Failed to decrypt github config (tampered or wrong key)")
        return None

    repo = _normalize_repo(str(data.get("repo") or ""))
    if not token.strip() or not repo:
        return None

    return DecryptedGitHubConfig(
        token=token.strip(),
        repo=repo,
        branch=_normalize_branch(str(data.get("branch") or DEFAULT_BRANCH)),
        base_path=_normalize_base_path(
            None if "base_path" not in data else str(data.get("base_path") or "")
        ),
    )


def mask_config(config_json: str | None) -> MaskedGitHubConfig:
    parsed = parse_config(config_json)
    data = _load_json(config_json)
    branch = _normalize_branch(str(data.get("branch") or DEFAULT_BRANCH))
    if "base_path" in data:
        base_path = _normalize_base_path(str(data.get("base_path") or ""))
    else:
        base_path = DEFAULT_BASE_PATH
    repo_public = _normalize_repo(str(data.get("repo") or "")) or None
    prefs = parse_preferences(config_json)

    if parsed is None:
        return MaskedGitHubConfig(
            configured=False,
            token_masked=None,
            repo=repo_public,
            branch=branch,
            base_path=base_path,
            notify_github_sync_in_app=prefs.notify_github_sync_in_app,
            notify_github_sync_telegram=prefs.notify_github_sync_telegram,
        )

    return MaskedGitHubConfig(
        configured=True,
        token_masked=_mask_token(parsed.token),
        repo=parsed.repo,
        branch=parsed.branch,
        base_path=parsed.base_path,
        notify_github_sync_in_app=prefs.notify_github_sync_in_app,
        notify_github_sync_telegram=prefs.notify_github_sync_telegram,
    )
