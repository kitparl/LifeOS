from datetime import date

import pytest

from app.modules.learning.seeder import SeedValidationError, resolve_seed_path


async def _auth(client, email: str):
    username = ("usr_" + email.split("@")[0].replace(".", "").replace("+", "").replace("-", "")[:26])
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "password123",
            "display_name": "Learner",
        },
    )
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.mark.asyncio
async def test_seed_idempotency_and_progress_preservation(client):
    h = await _auth(client, "track-seed@example.com")

    first = await client.post(
        "/api/v1/learning/tracks/seed",
        headers=h,
        json={"slug": "ai-systems-engineering"},
    )
    assert first.status_code == 201, first.text
    track = first.json()
    assert track["slug"] == "ai-systems-engineering"
    assert len(track["phases"]) == 10
    concepts_before = sum(len(p["concepts"]) for p in track["phases"])
    assert concepts_before >= 70

    phase = track["phases"][0]
    concept = phase["concepts"][0]
    patched = await client.patch(
        f"/api/v1/learning/concepts/{concept['id']}",
        headers=h,
        json={
            "can_explain": True,
            "confidence": 4,
            "artifact_url": "https://example.com/artifact",
            "failure_modes_known": True,
            "tradeoffs_known": True,
        },
    )
    assert patched.status_code == 200
    assert patched.json()["can_explain"] is True
    assert patched.json()["artifact_url"] == "https://example.com/artifact"

    progress = await client.get(f"/api/v1/learning/tracks/{track['id']}/progress", headers=h)
    assert progress.status_code == 200
    assert progress.json()["concepts_gated"] >= 1

    phase_item = await client.get(f"/api/v1/learning/items/{phase['id']}", headers=h)
    assert phase_item.status_code == 200
    assert phase_item.json()["progress"] > 0

    second = await client.post(
        "/api/v1/learning/tracks/seed",
        headers=h,
        json={"slug": "ai-systems-engineering"},
    )
    assert second.status_code == 201
    track2 = second.json()
    assert track2["id"] == track["id"]
    concepts_after = sum(len(p["concepts"]) for p in track2["phases"])
    assert concepts_after == concepts_before

    reloaded = await client.get(f"/api/v1/learning/concepts/{concept['id']}", headers=h)
    assert reloaded.status_code == 200
    body = reloaded.json()
    assert body["can_explain"] is True
    assert body["confidence"] == 4
    assert body["artifact_url"] == "https://example.com/artifact"
    assert body["failure_modes_known"] is True


@pytest.mark.asyncio
async def test_user_isolation(client):
    h1 = await _auth(client, "track-owner@example.com")
    h2 = await _auth(client, "track-other@example.com")

    seeded = await client.post(
        "/api/v1/learning/tracks/seed",
        headers=h1,
        json={"slug": "ai-systems-engineering"},
    )
    assert seeded.status_code == 201
    track_id = seeded.json()["id"]
    concept_id = seeded.json()["phases"][0]["concepts"][0]["id"]

    denied = await client.get(f"/api/v1/learning/tracks/{track_id}", headers=h2)
    assert denied.status_code == 404

    denied_patch = await client.patch(
        f"/api/v1/learning/concepts/{concept_id}",
        headers=h2,
        json={"can_explain": True},
    )
    assert denied_patch.status_code == 404

    other_list = await client.get("/api/v1/learning/tracks", headers=h2)
    assert other_list.status_code == 200
    assert other_list.json() == []


@pytest.mark.asyncio
async def test_seed_slug_rejection(client):
    h = await _auth(client, "track-slug@example.com")

    bad = await client.post(
        "/api/v1/learning/tracks/seed",
        headers=h,
        json={"slug": "../../etc/passwd"},
    )
    assert bad.status_code == 422  # pydantic pattern validation

    missing = await client.post(
        "/api/v1/learning/tracks/seed",
        headers=h,
        json={"slug": "does-not-exist-track"},
    )
    assert missing.status_code == 400

    with pytest.raises(SeedValidationError):
        resolve_seed_path("../../etc/passwd")


@pytest.mark.asyncio
async def test_every_concept_has_a_resource(client):
    h = await _auth(client, "track-resources@example.com")
    seeded = await client.post(
        "/api/v1/learning/tracks/seed",
        headers=h,
        json={"slug": "ai-systems-engineering"},
    )
    assert seeded.status_code == 201
    track = seeded.json()

    for phase in track["phases"]:
        assert phase["resources"], f"{phase['slug']} has no phase resources"
        for concept in phase["concepts"]:
            assert concept["resources"], f"{concept['slug']} has no resources"

    concept_id = track["phases"][0]["concepts"][0]["id"]
    detail = await client.get(f"/api/v1/learning/concepts/{concept_id}", headers=h)
    assert detail.status_code == 200
    assert detail.json()["inherited_resources"], "phase resources should be inherited by concepts"


@pytest.mark.asyncio
async def test_attach_note_to_new_and_existing_subject(client):
    h = await _auth(client, "track-notes@example.com")
    seeded = await client.post(
        "/api/v1/learning/tracks/seed",
        headers=h,
        json={"slug": "ai-systems-engineering"},
    )
    phase = seeded.json()["phases"][0]
    concept = phase["concepts"][0]
    other_concept = phase["concepts"][1]

    created = await client.post(
        f"/api/v1/learning/concepts/{concept['id']}/notes",
        headers=h,
        json={"subject_title": "AI Systems Engineering", "content": "Prefill vs decode costs differ."},
    )
    assert created.status_code == 201, created.text
    note = created.json()
    assert note["subject_title"] == "AI Systems Engineering"
    assert note["chapter_title"] == phase["title"]
    assert note["section_title"] == concept["title"]

    # The new subject shows up in knowledge notes and can be reused for another concept.
    subjects = await client.get("/api/v1/knowledge-notes/subjects", headers=h)
    assert [s["title"] for s in subjects.json()] == ["AI Systems Engineering"]
    subject_id = note["subject_id"]

    reused = await client.post(
        f"/api/v1/learning/concepts/{other_concept['id']}/notes",
        headers=h,
        json={"subject_id": subject_id, "title": "Tokenizer gotchas", "content": "JSON inflates tokens."},
    )
    assert reused.status_code == 201
    assert reused.json()["subject_id"] == subject_id
    # Same phase → same chapter, no duplicates.
    assert reused.json()["chapter_id"] == note["chapter_id"]

    listed = await client.get(f"/api/v1/learning/concepts/{concept['id']}/notes", headers=h)
    assert [n["id"] for n in listed.json()] == [note["id"]]

    unlinked = await client.delete(
        f"/api/v1/learning/concepts/{concept['id']}/notes/{note['id']}", headers=h
    )
    assert unlinked.status_code == 204
    after = await client.get(f"/api/v1/learning/concepts/{concept['id']}/notes", headers=h)
    assert after.json() == []
    # Unlinking keeps the note itself.
    still_there = await client.get(
        f"/api/v1/knowledge-notes/sections/{note['section_id']}", headers=h
    )
    assert still_there.status_code == 200


@pytest.mark.asyncio
async def test_concept_notes_are_user_isolated(client):
    h1 = await _auth(client, "notes-owner@example.com")
    h2 = await _auth(client, "notes-intruder@example.com")
    seeded = await client.post(
        "/api/v1/learning/tracks/seed", headers=h1, json={"slug": "ai-systems-engineering"}
    )
    concept_id = seeded.json()["phases"][0]["concepts"][0]["id"]

    created = await client.post(
        f"/api/v1/learning/concepts/{concept_id}/notes",
        headers=h1,
        json={"subject_title": "Owner notes", "content": "private"},
    )
    note_id = created.json()["id"]

    assert (
        await client.get(f"/api/v1/learning/concepts/{concept_id}/notes", headers=h2)
    ).status_code == 404
    assert (
        await client.delete(
            f"/api/v1/learning/concepts/{concept_id}/notes/{note_id}", headers=h2
        )
    ).status_code == 404


@pytest.mark.asyncio
async def test_session_log_and_stats(client):
    h = await _auth(client, "track-session@example.com")
    seeded = await client.post(
        "/api/v1/learning/tracks/seed",
        headers=h,
        json={"slug": "ai-systems-engineering"},
    )
    phase = seeded.json()["phases"][0]
    concept = phase["concepts"][0]

    session = await client.post(
        "/api/v1/learning/sessions",
        headers=h,
        json={
            "item_id": phase["id"],
            "concept_id": concept["id"],
            "session_date": date.today().isoformat(),
            "minutes": 45,
            "confidence": 3,
            "can_explain": True,
            "notes": "Wrote down decode loop in own words",
        },
    )
    assert session.status_code == 201

    stats = await client.get("/api/v1/learning/sessions/stats", headers=h)
    assert stats.status_code == 200
    assert stats.json()["minutes_this_week"] >= 45
    assert stats.json()["concepts_gated"] >= 1
