import pytest
from app.modules.planner.models import PlannerNode
from app.modules.planner.service import EMPTY_DIAGRAM_XML
from sqlalchemy import select

BASE = "/api/v1/planner/nodes"


async def _auth_token(client, email="planner@example.com"):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "username": ("usr_" + email.split("@")[0].replace(".", "").replace("+", "").replace("-", "")[:26]),
            "email": email,
            "password": "password123",
            "display_name": "Planner User",
        },
    )
    return {"Authorization": f"Bearer {reg.json()['access_token']}"}


async def _make(client, headers, kind, name, parent_id=None):
    resp = await client.post(BASE, headers=headers, json={"kind": kind, "name": name, "parent_id": parent_id})
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _names(client, headers, parent_id):
    resp = await client.get(BASE, headers=headers)
    assert resp.status_code == 200
    nodes = [n for n in resp.json() if n["parent_id"] == parent_id]
    return [n["name"] for n in sorted(nodes, key=lambda n: n["order_index"])], nodes


@pytest.mark.asyncio
async def test_create_project_folder_diagram_and_list(client):
    h = await _auth_token(client)
    project = await _make(client, h, "project", "P")
    folder = await _make(client, h, "folder", "F", project["id"])
    diagram = await _make(client, h, "diagram", "D", folder["id"])
    assert diagram["revision"] == 1
    assert project["order_index"] == 0

    listing = await client.get(BASE, headers=h)
    assert listing.status_code == 200
    assert len(listing.json()) == 3
    assert all("content" not in n for n in listing.json())


@pytest.mark.asyncio
async def test_kind_parent_rules(client):
    h = await _auth_token(client)
    project = await _make(client, h, "project", "P")
    folder = await _make(client, h, "folder", "F", project["id"])
    diagram = await _make(client, h, "diagram", "D", folder["id"])

    r = await client.post(BASE, headers=h, json={"kind": "folder", "name": "X"})
    assert r.status_code == 400
    r = await client.post(BASE, headers=h, json={"kind": "project", "name": "X", "parent_id": project["id"]})
    assert r.status_code == 400
    r = await client.post(BASE, headers=h, json={"kind": "folder", "name": "X", "parent_id": diagram["id"]})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_name_validation(client):
    h = await _auth_token(client)
    for bad in ["  ", "a/b", "a\\b", "x" * 201]:
        r = await client.post(BASE, headers=h, json={"kind": "project", "name": bad})
        assert r.status_code == 422, bad
    ok = await client.post(BASE, headers=h, json={"kind": "project", "name": "  Plan "})
    assert ok.status_code == 201
    assert ok.json()["name"] == "Plan"


@pytest.mark.asyncio
async def test_sibling_name_conflict_case_insensitive(client):
    h = await _auth_token(client)
    p1 = await _make(client, h, "project", "P1")
    p2 = await _make(client, h, "project", "P2")
    await _make(client, h, "folder", "Auth", p1["id"])
    r = await client.post(BASE, headers=h, json={"kind": "folder", "name": "auth", "parent_id": p1["id"]})
    assert r.status_code == 409
    r = await client.post(BASE, headers=h, json={"kind": "folder", "name": "auth", "parent_id": p2["id"]})
    assert r.status_code == 201

    gone = await _make(client, h, "folder", "Old", p1["id"])
    assert (await client.delete(f"{BASE}/{gone['id']}", headers=h)).status_code == 204
    r = await client.post(BASE, headers=h, json={"kind": "folder", "name": "old", "parent_id": p1["id"]})
    assert r.status_code == 201

    # rename and move also enforce uniqueness
    other = await _make(client, h, "folder", "Other", p1["id"])
    r = await client.patch(f"{BASE}/{other['id']}", headers=h, json={"name": "AUTH"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_move_into_own_descendant_rejected(client):
    h = await _auth_token(client)
    project = await _make(client, h, "project", "P")
    a = await _make(client, h, "folder", "A", project["id"])
    b = await _make(client, h, "folder", "B", a["id"])
    r = await client.patch(f"{BASE}/{a['id']}", headers=h, json={"parent_id": b["id"]})
    assert r.status_code == 400
    r = await client.patch(f"{BASE}/{a['id']}", headers=h, json={"parent_id": a["id"]})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_move_reorders_siblings(client):
    h = await _auth_token(client)
    project = await _make(client, h, "project", "P")
    await _make(client, h, "folder", "x", project["id"])
    y = await _make(client, h, "folder", "y", project["id"])
    z = await _make(client, h, "folder", "z", project["id"])
    target = await _make(client, h, "folder", "target", project["id"])

    r = await client.patch(f"{BASE}/{z['id']}", headers=h, json={"order_index": 0})
    assert r.status_code == 200
    names, nodes = await _names(client, h, project["id"])
    assert names == ["z", "x", "y", "target"]
    assert sorted(n["order_index"] for n in nodes) == [0, 1, 2, 3]

    r = await client.patch(f"{BASE}/{y['id']}", headers=h, json={"parent_id": target["id"]})
    assert r.status_code == 200
    names, nodes = await _names(client, h, project["id"])
    assert names == ["z", "x", "target"]
    assert sorted(n["order_index"] for n in nodes) == [0, 1, 2]
    names, _ = await _names(client, h, target["id"])
    assert names == ["y"]

    # order_index is clamped
    r = await client.patch(f"{BASE}/{z['id']}", headers=h, json={"order_index": 99})
    assert r.status_code == 200
    names, _ = await _names(client, h, project["id"])
    assert names == ["x", "target", "z"]


@pytest.mark.asyncio
async def test_duplicate_subtree_names_and_content(client):
    h = await _auth_token(client)
    project = await _make(client, h, "project", "P")
    folder = await _make(client, h, "folder", "F", project["id"])
    diagram = await _make(client, h, "diagram", "D", folder["id"])

    first = await client.post(f"{BASE}/{folder['id']}/duplicate", headers=h)
    second = await client.post(f"{BASE}/{folder['id']}/duplicate", headers=h)
    assert first.status_code == 201 and second.status_code == 201
    assert first.json()["name"] == "F copy"
    assert second.json()["name"] == "F copy 2"
    assert first.json()["order_index"] == folder["order_index"] + 1

    async with client.session_factory() as session:
        rows = (await session.execute(select(PlannerNode))).scalars().all()
    original = next(n for n in rows if n.id == diagram["id"])
    copy_child = next(n for n in rows if n.parent_id == first.json()["id"])
    assert copy_child.id != original.id
    assert copy_child.name == "D"
    assert copy_child.content == original.content == EMPTY_DIAGRAM_XML
    assert copy_child.revision == 1


@pytest.mark.asyncio
async def test_delete_soft_deletes_subtree(client):
    h = await _auth_token(client)
    project = await _make(client, h, "project", "P")
    folder = await _make(client, h, "folder", "F", project["id"])
    diagram = await _make(client, h, "diagram", "D", folder["id"])

    assert (await client.delete(f"{BASE}/{folder['id']}", headers=h)).status_code == 204
    ids = [n["id"] for n in (await client.get(BASE, headers=h)).json()]
    assert ids == [project["id"]]

    async with client.session_factory() as session:
        row = (await session.execute(select(PlannerNode).where(PlannerNode.id == diagram["id"]))).scalar_one()
    assert row.deleted_at is not None


@pytest.mark.asyncio
async def test_other_user_gets_404(client):
    h1 = await _auth_token(client, "owner@example.com")
    h2 = await _auth_token(client, "intruder@example.com")
    project = await _make(client, h1, "project", "P")
    folder = await _make(client, h1, "folder", "F", project["id"])

    assert (await client.patch(f"{BASE}/{folder['id']}", headers=h2, json={"name": "Z"})).status_code == 404
    assert (await client.delete(f"{BASE}/{folder['id']}", headers=h2)).status_code == 404
    assert (await client.post(f"{BASE}/{folder['id']}/duplicate", headers=h2)).status_code == 404
    r = await client.post(BASE, headers=h2, json={"kind": "folder", "name": "X", "parent_id": project["id"]})
    assert r.status_code == 404
    assert (await client.get(BASE, headers=h2)).json() == []


@pytest.mark.asyncio
async def test_create_after_delete_keeps_order_indices_unique(client):
    h = await _auth_token(client)
    project = await _make(client, h, "project", "P")
    first = await _make(client, h, "folder", "a", project["id"])
    await _make(client, h, "folder", "b", project["id"])
    await _make(client, h, "folder", "c", project["id"])

    assert (await client.delete(f"{BASE}/{first['id']}", headers=h)).status_code == 204
    await _make(client, h, "folder", "d", project["id"])

    names, nodes = await _names(client, h, project["id"])
    assert names == ["b", "c", "d"]
    assert sorted(n["order_index"] for n in nodes) == [0, 1, 2]


def _content_url(node_id):
    return f"{BASE}/{node_id}/content"


async def _new_diagram(client, headers):
    project = await _make(client, headers, "project", "P")
    return await _make(client, headers, "diagram", "D", project["id"]), project


@pytest.mark.asyncio
async def test_new_diagram_content_is_empty_model(client):
    h = await _auth_token(client)
    diagram, _ = await _new_diagram(client, h)
    r = await client.get(_content_url(diagram["id"]), headers=h)
    assert r.status_code == 200
    assert "<mxGraphModel" in r.json()["content"]
    assert r.json()["revision"] == 1


@pytest.mark.asyncio
async def test_save_increments_revision(client):
    h = await _auth_token(client)
    diagram, _ = await _new_diagram(client, h)
    r = await client.put(_content_url(diagram["id"]), headers=h, json={"content": "<a/>", "base_revision": 1})
    assert r.status_code == 200
    assert r.json() == {"content": "<a/>", "revision": 2}
    got = await client.get(_content_url(diagram["id"]), headers=h)
    assert got.json() == {"content": "<a/>", "revision": 2}


@pytest.mark.asyncio
async def test_stale_base_revision_conflicts(client):
    h = await _auth_token(client)
    diagram, _ = await _new_diagram(client, h)
    first = await client.put(_content_url(diagram["id"]), headers=h, json={"content": "<a/>", "base_revision": 1})
    assert first.status_code == 200
    second = await client.put(_content_url(diagram["id"]), headers=h, json={"content": "<b/>", "base_revision": 1})
    assert second.status_code == 409
    got = await client.get(_content_url(diagram["id"]), headers=h)
    assert got.json() == {"content": "<a/>", "revision": 2}


@pytest.mark.asyncio
async def test_content_on_folder_rejected(client):
    h = await _auth_token(client)
    _, project = await _new_diagram(client, h)
    folder = await _make(client, h, "folder", "F", project["id"])
    assert (await client.get(_content_url(folder["id"]), headers=h)).status_code == 400
    r = await client.put(_content_url(folder["id"]), headers=h, json={"content": "<a/>", "base_revision": 1})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_content_too_large(client):
    h = await _auth_token(client)
    diagram, _ = await _new_diagram(client, h)
    at_limit = "x" * (5 * 1024 * 1024)
    ok = await client.put(_content_url(diagram["id"]), headers=h, json={"content": at_limit, "base_revision": 1})
    assert ok.status_code == 200
    r = await client.put(
        _content_url(diagram["id"]), headers=h, json={"content": at_limit + "x", "base_revision": 2}
    )
    assert r.status_code == 413


@pytest.mark.asyncio
async def test_content_other_user_404(client):
    owner = await _auth_token(client, "owner@example.com")
    other = await _auth_token(client, "other@example.com")
    diagram, _ = await _new_diagram(client, owner)
    assert (await client.get(_content_url(diagram["id"]), headers=other)).status_code == 404
    r = await client.put(_content_url(diagram["id"]), headers=other, json={"content": "<a/>", "base_revision": 1})
    assert r.status_code == 404
