"""Thin async adapter for GitHub REST + Git Data API. Never logs tokens."""

from __future__ import annotations

import asyncio
import base64
import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

_TRANSIENT_STATUS = frozenset({408, 429, 500, 502, 503, 504})
_MAX_RETRIES = 3


class GitHubClientError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.code = code or _classify_code(status_code, message)


def _classify_code(status_code: int | None, message: str) -> str:
    if status_code == 401:
        return "auth"
    if status_code == 403:
        return "permission"
    if status_code == 404:
        return "not_found"
    if status_code == 409:
        return "conflict"
    if status_code == 422:
        return "validation"
    if status_code in _TRANSIENT_STATUS or "timed out" in (message or "").lower():
        return "transient"
    if status_code and status_code >= 500:
        return "transient"
    return "unknown"


def user_facing_github_error(exc: GitHubClientError) -> str:
    if exc.code == "auth":
        return "Invalid or expired GitHub token. Update your PAT in Integrations."
    if exc.code == "permission":
        return "GitHub permission denied. Ensure the token has Contents: Read and write on this repo."
    if exc.code == "not_found":
        return "Repository or branch not found. Check owner/repo and branch."
    if exc.code == "conflict":
        return "Git conflict on GitHub. Try syncing again."
    if exc.code == "validation":
        return "GitHub rejected the request. Check file paths and content."
    if exc.code == "transient":
        return "GitHub is temporarily unavailable. Try again shortly."
    return str(exc) or "GitHub request failed"


@dataclass(frozen=True)
class GitHubFileMeta:
    path: str
    sha: str


@dataclass(frozen=True)
class TreeEntry:
    path: str
    sha: str | None  # None = delete
    mode: str = "100644"
    type: str = "blob"


@dataclass(frozen=True)
class AtomicCommitResult:
    commit_sha: str
    tree_sha: str


class GitHubClient:
    def __init__(
        self,
        token: str,
        owner: str,
        repo: str,
        *,
        branch: str = "main",
        base_url: str = "https://api.github.com",
        timeout: float = 30.0,
    ):
        if not token or not token.strip():
            raise GitHubClientError("GitHub token is required", code="auth")
        if not owner or not repo:
            raise GitHubClientError("GitHub owner/repo is required", code="validation")
        self._token = token.strip()
        self._owner = owner.strip()
        self._repo = repo.strip()
        self._branch = (branch or "main").strip()
        self._base = base_url.rstrip("/")
        self._timeout = timeout

    @classmethod
    def from_repo_slug(cls, token: str, repo_slug: str, *, branch: str = "main") -> GitHubClient:
        parts = repo_slug.split("/", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise GitHubClientError("Repository must be owner/name", code="validation")
        return cls(token, parts[0], parts[1], branch=branch)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _repo_url(self, suffix: str = "") -> str:
        return f"{self._base}/repos/{self._owner}/{self._repo}{suffix}"

    def _contents_url(self, path: str) -> str:
        encoded = quote(path.lstrip("/"), safe="/")
        return self._repo_url(f"/contents/{encoded}")

    async def _request(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        allow_404: bool = True,
    ) -> dict[str, Any] | None:
        last_exc: GitHubClientError | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.request(
                        method,
                        url,
                        headers=self._headers(),
                        json=json,
                        params=params,
                    )
            except httpx.TimeoutException as exc:
                last_exc = GitHubClientError("GitHub request timed out", code="transient")
                if attempt + 1 < _MAX_RETRIES:
                    await asyncio.sleep(0.4 * (2**attempt))
                    continue
                raise last_exc from exc
            except httpx.HTTPError as exc:
                raise GitHubClientError("GitHub request failed", code="unknown") from exc

            if response.status_code == 404 and allow_404:
                return None

            if response.status_code in _TRANSIENT_STATUS and attempt + 1 < _MAX_RETRIES:
                await asyncio.sleep(0.4 * (2**attempt))
                continue

            if response.status_code >= 400:
                detail = response.text[:300] if response.text else response.reason_phrase
                raise GitHubClientError(
                    f"GitHub API error ({response.status_code}): {detail}",
                    status_code=response.status_code,
                )

            if response.status_code == 204 or not response.content:
                return {}
            data = response.json()
            return data if isinstance(data, dict) else {}

        if last_exc:
            raise last_exc
        return None

    async def get_repo(self) -> dict[str, Any]:
        result = await self._request("GET", self._repo_url(), allow_404=True)
        if result is None:
            raise GitHubClientError("Repository not found", status_code=404)
        return result

    async def get_branch_ref(self) -> dict[str, Any]:
        url = self._repo_url(f"/git/ref/heads/{quote(self._branch, safe='')}")
        result = await self._request("GET", url, allow_404=True)
        if result is None:
            raise GitHubClientError(
                f"Branch '{self._branch}' not found",
                status_code=404,
            )
        return result

    async def get_file(self, path: str) -> GitHubFileMeta | None:
        data = await self._request(
            "GET",
            self._contents_url(path),
            params={"ref": self._branch},
            allow_404=True,
        )
        if not data:
            return None
        sha = data.get("sha")
        if not isinstance(sha, str):
            return None
        return GitHubFileMeta(path=path, sha=sha)

    async def put_file(
        self,
        path: str,
        content: bytes,
        message: str,
        *,
        sha: str | None = None,
    ) -> GitHubFileMeta:
        payload: dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(content).decode("ascii"),
            "branch": self._branch,
        }
        if sha:
            payload["sha"] = sha

        data = await self._request("PUT", self._contents_url(path), json=payload, allow_404=False)
        if not data:
            raise GitHubClientError("Unexpected empty response from GitHub")
        content_obj = data.get("content") if isinstance(data.get("content"), dict) else data
        new_sha = content_obj.get("sha") if isinstance(content_obj, dict) else data.get("sha")
        if not isinstance(new_sha, str):
            raise GitHubClientError("GitHub did not return file sha")
        return GitHubFileMeta(path=path, sha=new_sha)

    async def delete_file(self, path: str, sha: str, message: str) -> None:
        payload = {
            "message": message,
            "sha": sha,
            "branch": self._branch,
        }
        await self._request("DELETE", self._contents_url(path), json=payload, allow_404=False)

    async def create_blob(self, content: bytes) -> str:
        data = await self._request(
            "POST",
            self._repo_url("/git/blobs"),
            json={
                "content": base64.b64encode(content).decode("ascii"),
                "encoding": "base64",
            },
            allow_404=False,
        )
        if not data or not isinstance(data.get("sha"), str):
            raise GitHubClientError("GitHub did not return blob sha")
        return data["sha"]

    async def create_tree(self, base_tree_sha: str, entries: list[TreeEntry]) -> str:
        tree_payload = []
        for entry in entries:
            item: dict[str, Any] = {
                "path": entry.path,
                "mode": entry.mode,
                "type": entry.type,
            }
            if entry.sha is None:
                item["sha"] = None
            else:
                item["sha"] = entry.sha
            tree_payload.append(item)

        data = await self._request(
            "POST",
            self._repo_url("/git/trees"),
            json={"base_tree": base_tree_sha, "tree": tree_payload},
            allow_404=False,
        )
        if not data or not isinstance(data.get("sha"), str):
            raise GitHubClientError("GitHub did not return tree sha")
        return data["sha"]

    async def list_tree_blob_paths(self, tree_sha: str) -> set[str]:
        """Return blob paths in a tree (recursive). Used to skip deletes of missing files."""
        data = await self._request(
            "GET",
            self._repo_url(f"/git/trees/{tree_sha}"),
            params={"recursive": "1"},
            allow_404=False,
        )
        if not data:
            return set()
        paths: set[str] = set()
        for item in data.get("tree") or []:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "blob":
                continue
            path = item.get("path")
            if isinstance(path, str) and path:
                paths.add(path)
        return paths

    async def create_commit(self, message: str, tree_sha: str, parent_sha: str) -> str:
        data = await self._request(
            "POST",
            self._repo_url("/git/commits"),
            json={
                "message": message,
                "tree": tree_sha,
                "parents": [parent_sha],
            },
            allow_404=False,
        )
        if not data or not isinstance(data.get("sha"), str):
            raise GitHubClientError("GitHub did not return commit sha")
        return data["sha"]

    async def update_ref(self, commit_sha: str, *, force: bool = False) -> None:
        url = self._repo_url(f"/git/refs/heads/{quote(self._branch, safe='')}")
        await self._request(
            "PATCH",
            url,
            json={"sha": commit_sha, "force": force},
            allow_404=False,
        )

    async def commit_tree_changes(
        self,
        message: str,
        entries: list[TreeEntry],
    ) -> AtomicCommitResult:
        """Create blobs (caller supplies entry.sha) then one tree+commit+ref update.

        Deletes for paths that no longer exist on the remote tip are skipped so
        manual GitHub deletions / renames do not 422 the whole sync.
        """
        if not entries:
            raise GitHubClientError("No tree changes to commit", code="validation")

        ref = await self.get_branch_ref()
        obj = ref.get("object") if isinstance(ref.get("object"), dict) else {}
        parent_sha = obj.get("sha")
        if not isinstance(parent_sha, str):
            raise GitHubClientError("Could not resolve branch tip commit", code="not_found")

        commit = await self._request("GET", self._repo_url(f"/git/commits/{parent_sha}"), allow_404=False)
        if not commit:
            raise GitHubClientError("Could not load tip commit", code="not_found")
        tree_obj = commit.get("tree") if isinstance(commit.get("tree"), dict) else {}
        base_tree = tree_obj.get("sha")
        if not isinstance(base_tree, str):
            raise GitHubClientError("Could not resolve base tree", code="not_found")

        deletes = [e for e in entries if e.sha is None]
        writes = [e for e in entries if e.sha is not None]
        if deletes:
            existing = await self.list_tree_blob_paths(base_tree)
            deletes = [e for e in deletes if e.path in existing]
        filtered = writes + deletes
        if not filtered:
            # Only deletes of paths already gone on GitHub — nothing to commit.
            return AtomicCommitResult(commit_sha=parent_sha, tree_sha=base_tree)

        new_tree = await self.create_tree(base_tree, filtered)
        commit_sha = await self.create_commit(message, new_tree, parent_sha)
        await self.update_ref(commit_sha)
        return AtomicCommitResult(commit_sha=commit_sha, tree_sha=new_tree)

    async def validate_access(self) -> dict[str, Any]:
        """Check token, repo, branch, and write capability. Returns structured result."""
        repo = await self.get_repo()
        permissions = repo.get("permissions") if isinstance(repo.get("permissions"), dict) else {}
        can_push = bool(permissions.get("push") or permissions.get("admin"))
        if not can_push:
            raise GitHubClientError(
                "Token can read the repo but cannot push. Grant Contents: Write.",
                status_code=403,
            )
        await self.get_branch_ref()
        return {
            "full_name": repo.get("full_name") or f"{self._owner}/{self._repo}",
            "branch": self._branch,
            "can_push": True,
        }
