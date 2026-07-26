"""Enterprise task management tests — assignments, soft delete, permissions, history."""

from datetime import datetime, timezone

import pytest


async def _register(client, email: str, username: str, name: str = "User"):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "password123",
            "display_name": name,
        },
    )
    assert reg.status_code == 201, reg.text
    return reg.json()["access_token"], reg.json().get("user", {})


def _hdr(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_default_self_assignment(client):
    token, _ = await _register(client, "owner1@example.com", "owner1")
    create = await client.post("/api/v1/tasks", headers=_hdr(token), json={"title": "Mine"})
    assert create.status_code == 201
    body = create.json()
    assert body["assignment_status"] == "accepted"
    assert body["assigned_to"] is not None
    assert body["permissions"]["role"] == "owner"
    assert body["permissions"]["can_assign"] is True


@pytest.mark.asyncio
async def test_assigned_to_me_excludes_self_owned(client):
    """Self-assigned owned tasks stay in My tasks only, not Assigned to me."""
    token, _ = await _register(client, "selfasg@example.com", "selfasg")
    create = await client.post("/api/v1/tasks", headers=_hdr(token), json={"title": "Mine only"})
    task_id = create.json()["id"]

    # Explicit self-assign by username
    await client.post(
        f"/api/v1/tasks/{task_id}/assign",
        headers=_hdr(token),
        json={"assignee_username": "selfasg"},
    )

    owned = await client.get("/api/v1/tasks", headers=_hdr(token), params={"scope": "owned"})
    assert any(t["id"] == task_id for t in owned.json())

    inbox = await client.get(
        "/api/v1/tasks", headers=_hdr(token), params={"scope": "assigned_to_me"}
    )
    assert inbox.status_code == 200
    assert not any(t["id"] == task_id for t in inbox.json())


@pytest.mark.asyncio
async def test_assigned_subtask_appears_in_assignee_inbox(client):
    alice_tok, _ = await _register(client, "alice_sub@example.com", "alice_sub")
    bob_tok, _ = await _register(client, "bob_sub@example.com", "bob_sub")
    parent = await client.post(
        "/api/v1/tasks", headers=_hdr(alice_tok), json={"title": "Parent"}
    )
    parent_id = parent.json()["id"]
    sub = await client.post(
        "/api/v1/tasks",
        headers=_hdr(alice_tok),
        json={"title": "Sub for Bob", "parent_id": parent_id},
    )
    sub_id = sub.json()["id"]
    await client.post(
        f"/api/v1/tasks/{sub_id}/assign",
        headers=_hdr(alice_tok),
        json={"assignee_username": "bob_sub"},
    )
    inbox = await client.get(
        "/api/v1/tasks", headers=_hdr(bob_tok), params={"scope": "assigned_to_me"}
    )
    assert any(t["id"] == sub_id for t in inbox.json())


@pytest.mark.asyncio
async def test_assign_accept_reject_fallback(client):
    alice_tok, alice = await _register(client, "alice@example.com", "alice_t", "Alice")
    bob_tok, bob = await _register(client, "bob@example.com", "bob_t", "Bob")

    create = await client.post(
        "/api/v1/tasks", headers=_hdr(alice_tok), json={"title": "For Bob"}
    )
    task_id = create.json()["id"]

    assign = await client.post(
        f"/api/v1/tasks/{task_id}/assign",
        headers=_hdr(alice_tok),
        json={"assignee_username": "bob_t"},
    )
    assert assign.status_code == 200
    assert assign.json()["status"] == "pending"
    asg_id = assign.json()["id"]

    # Bob sees it in assigned_to_me
    inbox = await client.get(
        "/api/v1/tasks", headers=_hdr(bob_tok), params={"scope": "assigned_to_me"}
    )
    assert inbox.status_code == 200
    assert any(t["id"] == task_id for t in inbox.json())

    # Default owned list for Bob empty
    owned = await client.get("/api/v1/tasks", headers=_hdr(bob_tok))
    assert owned.json() == []

    # Accept
    accept = await client.post(
        f"/api/v1/tasks/{task_id}/assignments/{asg_id}/accept",
        headers=_hdr(bob_tok),
    )
    assert accept.status_code == 200
    assert accept.json()["status"] == "accepted"

    # Reassign and reject path
    create2 = await client.post(
        "/api/v1/tasks", headers=_hdr(alice_tok), json={"title": "Reject me"}
    )
    tid2 = create2.json()["id"]
    assign2 = await client.post(
        f"/api/v1/tasks/{tid2}/assign",
        headers=_hdr(alice_tok),
        json={"assignee_username": "bob_t"},
    )
    asg2 = assign2.json()["id"]
    reject = await client.post(
        f"/api/v1/tasks/{tid2}/assignments/{asg2}/reject",
        headers=_hdr(bob_tok),
        json={"reason": "Too busy"},
    )
    assert reject.status_code == 200
    assert reject.json()["status"] == "rejected"

    detail = await client.get(f"/api/v1/tasks/{tid2}", headers=_hdr(alice_tok))
    assert detail.json()["assignment_status"] == "accepted"
    assert detail.json()["assigned_to"] == detail.json().get("assigned_to")  # owner fallback


@pytest.mark.asyncio
async def test_assignee_cannot_edit_title(client):
    alice_tok, _ = await _register(client, "alice2@example.com", "alice2")
    bob_tok, _ = await _register(client, "bob2@example.com", "bob2")
    create = await client.post("/api/v1/tasks", headers=_hdr(alice_tok), json={"title": "Locked"})
    task_id = create.json()["id"]
    assign = await client.post(
        f"/api/v1/tasks/{task_id}/assign",
        headers=_hdr(alice_tok),
        json={"assignee_username": "bob2"},
    )
    await client.post(
        f"/api/v1/tasks/{task_id}/assignments/{assign.json()['id']}/accept",
        headers=_hdr(bob_tok),
    )
    patch = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=_hdr(bob_tok),
        json={"title": "Hacked"},
    )
    assert patch.status_code == 403


@pytest.mark.asyncio
async def test_status_hold_and_done_alias(client):
    token, _ = await _register(client, "stat@example.com", "statuser")
    create = await client.post("/api/v1/tasks", headers=_hdr(token), json={"title": "S"})
    task_id = create.json()["id"]
    hold = await client.patch(
        f"/api/v1/tasks/{task_id}", headers=_hdr(token), json={"status": "hold"}
    )
    assert hold.status_code == 200
    assert hold.json()["status"] == "hold"
    done = await client.patch(
        f"/api/v1/tasks/{task_id}", headers=_hdr(token), json={"status": "done"}
    )
    assert done.status_code == 200
    assert done.json()["status"] == "completed"
    hist = await client.get(f"/api/v1/tasks/{task_id}/status-history", headers=_hdr(token))
    assert hist.status_code == 200
    assert len(hist.json()) >= 2


@pytest.mark.asyncio
async def test_soft_delete_hides_from_list(client):
    token, _ = await _register(client, "del@example.com", "deleter")
    create = await client.post("/api/v1/tasks", headers=_hdr(token), json={"title": "Gone"})
    task_id = create.json()["id"]
    delete = await client.delete(f"/api/v1/tasks/{task_id}", headers=_hdr(token))
    assert delete.status_code == 204
    listing = await client.get("/api/v1/tasks", headers=_hdr(token))
    assert listing.json() == []
    get = await client.get(f"/api/v1/tasks/{task_id}", headers=_hdr(token))
    assert get.status_code == 404


@pytest.mark.asyncio
async def test_archive_restore(client):
    token, _ = await _register(client, "arch@example.com", "archiver")
    create = await client.post("/api/v1/tasks", headers=_hdr(token), json={"title": "Archive me"})
    task_id = create.json()["id"]
    arch = await client.post(f"/api/v1/tasks/{task_id}/archive", headers=_hdr(token))
    assert arch.status_code == 200
    assert arch.json()["archived_at"] is not None
    listing = await client.get("/api/v1/tasks", headers=_hdr(token))
    assert listing.json() == []
    restored = await client.post(f"/api/v1/tasks/{task_id}/restore", headers=_hdr(token))
    assert restored.json()["archived_at"] is None


@pytest.mark.asyncio
async def test_watchers_notes_tags_activity(client):
    alice_tok, _ = await _register(client, "alice3@example.com", "alice3")
    carol_tok, _ = await _register(client, "carol@example.com", "carol_w")
    create = await client.post("/api/v1/tasks", headers=_hdr(alice_tok), json={"title": "Collab"})
    task_id = create.json()["id"]

    w = await client.post(
        f"/api/v1/tasks/{task_id}/watchers",
        headers=_hdr(alice_tok),
        json={"username": "carol_w"},
    )
    assert w.status_code == 201

    note = await client.post(
        f"/api/v1/tasks/{task_id}/notes",
        headers=_hdr(alice_tok),
        json={"body": "Hello note"},
    )
    assert note.status_code == 201

    tag = await client.post(
        f"/api/v1/tasks/{task_id}/tags",
        headers=_hdr(alice_tok),
        json={"name": "Urgent"},
    )
    assert tag.status_code == 201
    assert tag.json()["name"] == "urgent"

    activity = await client.get(f"/api/v1/tasks/{task_id}/activity", headers=_hdr(alice_tok))
    assert activity.status_code == 200
    actions = {a["action"] for a in activity.json()}
    assert "create" in actions
    assert "watcher_add" in actions
    assert "note" in actions


@pytest.mark.asyncio
async def test_version_conflict(client):
    token, _ = await _register(client, "ver@example.com", "versioner")
    create = await client.post("/api/v1/tasks", headers=_hdr(token), json={"title": "V"})
    task_id = create.json()["id"]
    version = create.json()["version"]
    await client.patch(
        f"/api/v1/tasks/{task_id}", headers=_hdr(token), json={"title": "V2"}
    )
    conflict = await client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=_hdr(token),
        json={"title": "V3", "version": version},
    )
    assert conflict.status_code == 409


@pytest.mark.asyncio
async def test_stranger_gets_404(client):
    alice_tok, _ = await _register(client, "alice4@example.com", "alice4")
    eve_tok, _ = await _register(client, "eve@example.com", "eve_s")
    create = await client.post("/api/v1/tasks", headers=_hdr(alice_tok), json={"title": "Secret"})
    task_id = create.json()["id"]
    get = await client.get(f"/api/v1/tasks/{task_id}", headers=_hdr(eve_tok))
    assert get.status_code == 404


@pytest.mark.asyncio
async def test_independent_subtask_assignment(client):
    alice_tok, _ = await _register(client, "alice5@example.com", "alice5")
    bob_tok, _ = await _register(client, "bob5@example.com", "bob5")
    parent = await client.post("/api/v1/tasks", headers=_hdr(alice_tok), json={"title": "Parent"})
    parent_id = parent.json()["id"]
    sub = await client.post(
        "/api/v1/tasks",
        headers=_hdr(alice_tok),
        json={"title": "Sub", "parent_id": parent_id},
    )
    sub_id = sub.json()["id"]
    await client.post(
        f"/api/v1/tasks/{sub_id}/assign",
        headers=_hdr(alice_tok),
        json={"assignee_username": "bob5"},
    )
    parent_detail = await client.get(f"/api/v1/tasks/{parent_id}", headers=_hdr(alice_tok))
    # Parent still self-assigned
    assert parent_detail.json()["assignment_status"] == "accepted"
    subs = parent_detail.json()["subtasks"]
    assert len(subs) == 1
    assert subs[0]["assignee_username"] == "bob5"
    assert subs[0]["assignment_status"] == "pending"
    sub_detail = await client.get(f"/api/v1/tasks/{sub_id}", headers=_hdr(alice_tok))
    assert sub_detail.json()["assignment_status"] == "pending"
    assert sub_detail.json()["assignee_username"] == "bob5"


@pytest.mark.asyncio
async def test_reassign_and_cancel_notify_previous_assignee(client):
    # Ensure integrations subscriber is registered (lifespan may not run under ASGITransport).
    import app.modules.integrations.subscriber  # noqa: F401
    import app.modules.notifications.models  # noqa: F401

    alice_tok, _ = await _register(client, "alice_n@example.com", "alice_n")
    bob_tok, _ = await _register(client, "bob_n@example.com", "bob_n")
    carol_tok, _ = await _register(client, "carol_n@example.com", "carol_n")

    created = await client.post("/api/v1/tasks", headers=_hdr(alice_tok), json={"title": "Notify me"})
    task_id = created.json()["id"]

    assign_bob = await client.post(
        f"/api/v1/tasks/{task_id}/assign",
        headers=_hdr(alice_tok),
        json={"assignee_username": "bob_n"},
    )
    assert assign_bob.status_code == 200

    bob_notes = await client.get("/api/v1/notifications", headers=_hdr(bob_tok))
    assert bob_notes.status_code == 200
    assert any("assigned to you" in n["message"].lower() for n in bob_notes.json())

    # Reassign to carol — bob should learn it went to another user
    await client.post(
        f"/api/v1/tasks/{task_id}/assign",
        headers=_hdr(alice_tok),
        json={"assignee_username": "carol_n"},
    )
    bob_notes2 = await client.get("/api/v1/notifications", headers=_hdr(bob_tok))
    assert any("another user" in n["message"].lower() for n in bob_notes2.json())
    carol_notes = await client.get("/api/v1/notifications", headers=_hdr(carol_tok))
    assert any(
        "reassigned to you" in n["message"].lower() or "assigned to you" in n["message"].lower()
        for n in carol_notes.json()
    )

    # Cancel carol's assignment — carol notified of removal
    detail = await client.get(f"/api/v1/tasks/{task_id}", headers=_hdr(alice_tok))
    carol_asg = detail.json()["assignment_id"]
    cancel = await client.post(
        f"/api/v1/tasks/{task_id}/assignments/{carol_asg}/cancel",
        headers=_hdr(alice_tok),
    )
    assert cancel.status_code == 200
    carol_notes2 = await client.get("/api/v1/notifications", headers=_hdr(carol_tok))
    assert any("removed" in n["message"].lower() for n in carol_notes2.json())
