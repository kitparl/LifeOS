"""Tests for GitHub Knowledge Notes sync helpers (v2 planner + atomic commit)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.integrations.github_client import (
    AtomicCommitResult,
    GitHubClientError,
    user_facing_github_error,
)
from app.modules.integrations.github_config import (
    _normalize_repo,
    mask_config,
    parse_config,
    parse_preferences,
    serialize_config,
)
from app.modules.integrations.github_slug import slugify
from app.modules.integrations.github_sync_planner import build_sync_plan
from app.modules.integrations.github_sync_service import (
    _asset_filename,
    _content_hash,
    build_paths,
    extract_file_ids,
    rewrite_markdown,
)
from app.modules.knowledge_notes.models import KnowledgeChapter, KnowledgeSection, KnowledgeSubject


def test_slugify():
    assert slugify("Python Basics") == "python-basics"
    assert slugify("  ") == "untitled"
    assert slugify("Variable, Types, Expressions") == "variable-types-expressions"
    assert slugify("Data Types: Numeric and Boolean") == "data-types-numeric-and-boolean"
    assert slugify("C++ / Basics!!!") == "c-basics"


def test_normalize_repo_accepts_urls():
    assert _normalize_repo("kitparl/engineering-notes") == "kitparl/engineering-notes"
    assert (
        _normalize_repo("https://github.com/kitparl/engineering-notes.git")
        == "kitparl/engineering-notes"
    )
    assert (
        _normalize_repo("https://github.com/kitparl/engineering-notes")
        == "kitparl/engineering-notes"
    )
    assert (
        _normalize_repo("git@github.com:kitparl/engineering-notes.git")
        == "kitparl/engineering-notes"
    )
    assert _normalize_repo("not a repo") == ""


def test_extract_file_ids():
    content = "![x](/api/v1/files/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/content)\n"
    assert extract_file_ids(content) == {"aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"}


def test_rewrite_markdown():
    file_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    content = f"![shot](/api/v1/files/{file_id}/content)"
    rewritten = rewrite_markdown(content, {file_id: "./assets/shot.png"})
    assert rewritten == "![shot](./assets/shot.png)"


def test_uuid_asset_filename():
    file_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    assert _asset_filename("shot.png", file_id) == f"{file_id}-shot.png"


def test_build_paths():
    subject = KnowledgeSubject(id="s1", user_id="u1", title="Python", order_index=0)
    chapter = KnowledgeChapter(id="c1", user_id="u1", subject_id="s1", title="Variables", order_index=0)
    section = KnowledgeSection(
        id="sec1",
        user_id="u1",
        chapter_id="c1",
        title="Intro",
        content="hello",
        order_index=0,
    )
    md_path, assets_dir = build_paths(subject, chapter, section, "")
    assert md_path == "python/variables/intro.md"
    assert assets_dir == "python/variables/assets"

    nested = build_paths(subject, chapter, section, "notes")
    assert nested[0] == "notes/python/variables/intro.md"


def test_content_hash_stable():
    h1 = _content_hash("# Title\n", {"id1": "abc"})
    h2 = _content_hash("# Title\n", {"id1": "abc"})
    h3 = _content_hash("# Title\nchanged", {"id1": "abc"})
    assert h1 == h2
    assert h1 != h3


def test_github_config_roundtrip():
    raw = serialize_config(
        token="ghp_testtoken1234",
        repo="user/repo",
        notify_github_sync_in_app=True,
        notify_github_sync_telegram=False,
        existing_json=None,
    )
    parsed = parse_config(raw)
    assert parsed is not None
    assert parsed.repo == "user/repo"
    assert parsed.token == "ghp_testtoken1234"
    masked = mask_config(raw)
    assert masked.configured is True
    assert masked.token_masked.endswith("1234")
    assert masked.notify_github_sync_in_app is True
    assert masked.notify_github_sync_telegram is False


def test_github_config_legacy_notify_toggle():
    import json

    legacy = json.dumps(
        {
            "token_enc": "",
            "repo": "user/repo",
            "branch": "main",
            "base_path": "",
            "notify_github_sync": True,
        }
    )
    prefs = parse_preferences(legacy)
    assert prefs.notify_github_sync_in_app is True
    assert prefs.notify_github_sync_telegram is True


def test_planner_noop_when_hash_matches():
    plan = build_sync_plan(
        md_path="notes/a/b/c.md",
        rewritten_md="hello",
        content_hash="abc",
        assets=[],
        previous_md_path="notes/a/b/c.md",
        previous_content_hash="abc",
        previous_assets=[],
    )
    assert plan.is_noop is True


def test_planner_rename_deletes_old_path():
    plan = build_sync_plan(
        md_path="notes/a/b/new.md",
        rewritten_md="hello",
        content_hash="newhash",
        assets=[],
        previous_md_path="notes/a/b/old.md",
        previous_content_hash="oldhash",
        previous_assets=[],
    )
    assert any(d.action == "delete" and d.path == "notes/a/b/old.md" for d in plan.deletes)
    assert any(f.action == "create" and f.path == "notes/a/b/new.md" for f in plan.files)


def test_planner_orphan_asset_delete():
    plan = build_sync_plan(
        md_path="notes/a/b/c.md",
        rewritten_md="hello",
        content_hash="newhash",
        assets=[],
        previous_md_path="notes/a/b/c.md",
        previous_content_hash="oldhash",
        previous_assets=[("fid1", "notes/a/b/assets/fid1-x.png", "sha1")],
    )
    assert any(d.path == "notes/a/b/assets/fid1-x.png" for d in plan.deletes)


def test_user_facing_github_error():
    assert "token" in user_facing_github_error(GitHubClientError("x", status_code=401)).lower()
    assert "permission" in user_facing_github_error(GitHubClientError("x", status_code=403)).lower()


@pytest.mark.asyncio
async def test_sync_section_unchanged_skips_commit():
    from app.modules.integrations.github_sync_service import GitHubSyncService

    subject = KnowledgeSubject(id="s1", user_id="u1", title="Python", order_index=0)
    chapter = KnowledgeChapter(id="c1", user_id="u1", subject_id="s1", title="Ch1", order_index=0)
    section = KnowledgeSection(
        id="sec1",
        user_id="u1",
        chapter_id="c1",
        title="Intro",
        content="plain text",
        order_index=0,
    )

    db = MagicMock()
    db.flush = AsyncMock()
    svc = GitHubSyncService(db)
    svc.integrations = MagicMock()
    conn = MagicMock()
    conn.enabled = True
    conn.config_json = serialize_config(token="tok", repo="user/repo")
    conn.last_sync_at = None
    svc.integrations.get_by_provider = AsyncMock(return_value=conn)

    svc._load_section_context = AsyncMock(
        return_value=MagicMock(section=section, chapter=chapter, subject=subject)
    )

    md_path, _ = build_paths(subject, chapter, section, "")
    content_hash = _content_hash("plain text", {})
    state = MagicMock()
    state.md_path = md_path
    state.content_hash = content_hash
    state.assets_json = "[]"
    state.md_sha = "mdsha"
    state.remote_commit_sha = "commit1"
    svc.sync_repo.get_by_section = AsyncMock(return_value=state)
    svc.sync_repo.set_status = AsyncMock(return_value=state)
    svc.sync_repo.upsert = AsyncMock(return_value=state)
    svc._apply_plan_atomic = AsyncMock()
    svc._client = MagicMock(
        return_value=MagicMock(get_file=AsyncMock(return_value=MagicMock(sha="remote")))
    )

    result = await svc.sync_section("u1", "sec1")

    assert result["status"] == "unchanged"
    assert "Already up to date" in result["message"]
    svc._apply_plan_atomic.assert_not_called()


@pytest.mark.asyncio
async def test_sync_section_recreates_when_remote_file_missing(monkeypatch):
    from app.modules.integrations import github_sync_service as sync_mod
    from app.modules.integrations.github_sync_service import GitHubSyncService

    monkeypatch.setattr(sync_mod, "notify_github_sync_result", AsyncMock())

    subject = KnowledgeSubject(id="s1", user_id="u1", title="Python", order_index=0)
    chapter = KnowledgeChapter(id="c1", user_id="u1", subject_id="s1", title="Ch1", order_index=0)
    section = KnowledgeSection(
        id="sec1",
        user_id="u1",
        chapter_id="c1",
        title="Intro",
        content="plain text",
        order_index=0,
    )

    db = MagicMock()
    db.flush = AsyncMock()
    svc = GitHubSyncService(db)
    svc.integrations = MagicMock()
    conn = MagicMock()
    conn.enabled = True
    conn.config_json = serialize_config(token="tok", repo="user/repo")
    conn.last_sync_at = None
    conn.status = "connected"
    svc.integrations.get_by_provider = AsyncMock(return_value=conn)

    svc._load_section_context = AsyncMock(
        return_value=MagicMock(section=section, chapter=chapter, subject=subject)
    )

    md_path, _ = build_paths(subject, chapter, section, "")
    content_hash = _content_hash("plain text", {})
    state = MagicMock()
    state.md_path = md_path
    state.content_hash = content_hash
    state.assets_json = "[]"
    state.md_sha = "mdsha"
    state.remote_commit_sha = "commit1"
    svc.sync_repo.get_by_section = AsyncMock(return_value=state)
    svc.sync_repo.set_status = AsyncMock(return_value=state)
    svc.sync_repo.upsert = AsyncMock(return_value=state)
    svc._apply_plan_atomic = AsyncMock(return_value=("newcommit", {md_path: "blob"}))
    svc._client = MagicMock(return_value=MagicMock(get_file=AsyncMock(return_value=None)))

    result = await svc.sync_section("u1", "sec1")

    assert result["status"] == "synced"
    assert result["message"] == "Pushed"
    svc._apply_plan_atomic.assert_awaited_once()
    plan = svc._apply_plan_atomic.await_args.args[2]
    assert any(f.action == "create" and f.path == md_path for f in plan.files)


@pytest.mark.asyncio
async def test_apply_plan_atomic_creates_blobs_and_commit():
    from app.modules.integrations.github_sync_service import GitHubSyncService
    from app.modules.integrations.github_sync_planner import PlannedFile, SyncPlan

    client = MagicMock()
    client.create_blob = AsyncMock(side_effect=["blob1", "blob2"])
    client.commit_tree_changes = AsyncMock(
        return_value=AtomicCommitResult(commit_sha="commitabc", tree_sha="tree1")
    )

    plan = SyncPlan(
        md_path="notes/a/b/c.md",
        content_hash="h",
        rewritten_md="# hi",
        assets=[("fid", "notes/a/b/assets/fid-x.png", b"img")],
        files=[
            PlannedFile(action="create", path="notes/a/b/c.md", content=b"# hi"),
            PlannedFile(action="create", path="notes/a/b/assets/fid-x.png", content=b"img"),
        ],
        deletes=[PlannedFile(action="delete", path="notes/a/b/old.md")],
    )

    svc = GitHubSyncService(MagicMock())
    commit_sha, path_to_sha = await svc._apply_plan_atomic(client, "msg", plan)
    assert commit_sha == "commitabc"
    assert path_to_sha["notes/a/b/c.md"] == "blob1"
    assert path_to_sha["notes/a/b/assets/fid-x.png"] == "blob2"
    assert client.create_blob.await_count == 2
    tree_entries = client.commit_tree_changes.await_args.args[1]
    assert any(e.path == "notes/a/b/old.md" and e.sha is None for e in tree_entries)


@pytest.mark.asyncio
async def test_commit_tree_changes_skips_missing_deletes():
    from app.modules.integrations.github_client import GitHubClient, TreeEntry

    client = GitHubClient("tok", "o", "r", branch="main")
    client.get_branch_ref = AsyncMock(return_value={"object": {"sha": "parent"}})
    client._request = AsyncMock(
        side_effect=[
            {"tree": {"sha": "basetree"}},  # get commit
        ]
    )
    client.list_tree_blob_paths = AsyncMock(return_value={"keep.md"})
    client.create_tree = AsyncMock(return_value="newtree")
    client.create_commit = AsyncMock(return_value="newcommit")
    client.update_ref = AsyncMock()

    result = await client.commit_tree_changes(
        "msg",
        [
            TreeEntry(path="keep.md", sha="blob1"),
            TreeEntry(path="already-gone.md", sha=None),
            TreeEntry(path="also-gone.md", sha=None),
        ],
    )
    assert result.commit_sha == "newcommit"
    sent = client.create_tree.await_args.args[1]
    assert [e.path for e in sent] == ["keep.md"]
    assert all(e.sha is not None for e in sent)


@pytest.mark.asyncio
async def test_commit_tree_changes_noop_when_only_missing_deletes():
    from app.modules.integrations.github_client import GitHubClient, TreeEntry

    client = GitHubClient("tok", "o", "r", branch="main")
    client.get_branch_ref = AsyncMock(return_value={"object": {"sha": "parent"}})
    client._request = AsyncMock(return_value={"tree": {"sha": "basetree"}})
    client.list_tree_blob_paths = AsyncMock(return_value=set())
    client.create_tree = AsyncMock()
    client.create_commit = AsyncMock()
    client.update_ref = AsyncMock()

    result = await client.commit_tree_changes(
        "msg",
        [TreeEntry(path="gone.md", sha=None)],
    )
    assert result.commit_sha == "parent"
    client.create_tree.assert_not_called()
    client.create_commit.assert_not_called()
    client.update_ref.assert_not_called()
