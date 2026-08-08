"""
Idempotent learning-track seeder.

Keyed on slug at every level. Never overwrites user progress fields:
confidence, can_explain, failure_modes_known, tradeoffs_known,
artifact_url, is_consumed, notes, completed_at.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.learning.models import (
    RESOURCE_PRIORITY,
    RESOURCE_TYPES,
    TRACK_STATUSES,
    LearningConcept,
    LearningItem,
    LearningResource,
    LearningTrack,
)

SEEDS_DIR = Path(__file__).resolve().parent / "seeds"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
PROGRESS_FIELDS_CONCEPT = frozenset(
    {
        "confidence",
        "can_explain",
        "failure_modes_known",
        "tradeoffs_known",
        "artifact_url",
        "completed_at",
    }
)
PROGRESS_FIELDS_RESOURCE = frozenset({"is_consumed", "notes"})


class SeedValidationError(ValueError):
    pass


def resolve_seed_path(slug: str) -> Path:
    if not SLUG_RE.match(slug) or slug.startswith("_"):
        raise SeedValidationError(f"Invalid seed slug: {slug!r}")
    path = (SEEDS_DIR / f"{slug}.json").resolve()
    if not str(path).startswith(str(SEEDS_DIR.resolve())):
        raise SeedValidationError("Seed path escapes seeds directory")
    if not path.is_file():
        raise SeedValidationError(f"Seed file not found: {slug}.json")
    return path


def _require(obj: dict, key: str, typ: type | tuple[type, ...]) -> Any:
    if key not in obj:
        raise SeedValidationError(f"Missing required field: {key}")
    val = obj[key]
    if not isinstance(val, typ):
        raise SeedValidationError(f"Field {key} must be {typ}, got {type(val).__name__}")
    return val


def validate_seed(data: dict[str, Any]) -> None:
    """Hand-rolled schema check against seeds/_schema.json contract (no jsonschema dep)."""
    _require(data, "slug", str)
    if not SLUG_RE.match(data["slug"]):
        raise SeedValidationError("track slug invalid")
    _require(data, "title", str)
    if "weekly_hours_target" in data and not isinstance(data["weekly_hours_target"], int):
        raise SeedValidationError("weekly_hours_target must be int")
    if "status" in data and data["status"] not in TRACK_STATUSES:
        raise SeedValidationError(f"status must be one of {TRACK_STATUSES}")
    phases = _require(data, "phases", list)
    for phase in phases:
        if not isinstance(phase, dict):
            raise SeedValidationError("phase must be object")
        _require(phase, "slug", str)
        _require(phase, "title", str)
        if "item_type" in phase and phase["item_type"] != "study_plan":
            raise SeedValidationError("phase item_type must be study_plan")
        concepts = phase.get("concepts", [])
        if not isinstance(concepts, list):
            raise SeedValidationError("concepts must be list")
        for concept in concepts:
            if not isinstance(concept, dict):
                raise SeedValidationError("concept must be object")
            _require(concept, "slug", str)
            _require(concept, "title", str)
            for res in concept.get("resources", []) + phase.get("resources", []):
                _validate_resource(res)


def _validate_resource(res: Any) -> None:
    if not isinstance(res, dict):
        raise SeedValidationError("resource must be object")
    _require(res, "title", str)
    _require(res, "url", str)
    rtype = res.get("resource_type", "article")
    if rtype not in RESOURCE_TYPES:
        raise SeedValidationError(f"resource_type must be one of {RESOURCE_TYPES}")
    priority = res.get("priority", "supporting")
    if priority not in RESOURCE_PRIORITY:
        raise SeedValidationError(f"priority must be one of {RESOURCE_PRIORITY}")


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


async def seed_track(db: AsyncSession, user_id: str, slug: str) -> LearningTrack:
    path = resolve_seed_path(slug)
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_seed(data)

    track = await _upsert_track(db, user_id, data)
    for idx, phase_data in enumerate(data.get("phases", [])):
        phase = await _upsert_phase(db, user_id, track, phase_data, idx + 1)
        for cidx, concept_data in enumerate(phase_data.get("concepts", [])):
            concept = await _upsert_concept(db, user_id, phase, concept_data, cidx + 1)
            for ridx, res_data in enumerate(concept_data.get("resources", [])):
                await _upsert_resource(
                    db, user_id, res_data, ridx + 1, item_id=phase.id, concept_id=concept.id
                )
        for ridx, res_data in enumerate(phase_data.get("resources", [])):
            await _upsert_resource(
                db, user_id, res_data, ridx + 1, item_id=phase.id, concept_id=None
            )
    await db.flush()
    return track


async def _upsert_track(db: AsyncSession, user_id: str, data: dict) -> LearningTrack:
    from sqlalchemy import select

    result = await db.execute(
        select(LearningTrack).where(LearningTrack.user_id == user_id, LearningTrack.slug == data["slug"])
    )
    track = result.scalar_one_or_none()
    fields = {
        "title": data["title"],
        "description": data.get("description"),
        "status": data.get("status", "planned"),
        "start_date": _parse_date(data.get("start_date")),
        "target_date": _parse_date(data.get("target_date")),
        "weekly_hours_target": data.get("weekly_hours_target", 11),
        "sort_order": data.get("sort_order", 0),
    }
    if track is None:
        track = LearningTrack(user_id=user_id, slug=data["slug"], **fields)
        db.add(track)
        await db.flush()
    else:
        for k, v in fields.items():
            setattr(track, k, v)
        await db.flush()
    return track


async def _upsert_phase(
    db: AsyncSession, user_id: str, track: LearningTrack, data: dict, sort_order: int
) -> LearningItem:
    from sqlalchemy import select

    result = await db.execute(
        select(LearningItem).where(
            LearningItem.user_id == user_id,
            LearningItem.track_id == track.id,
            LearningItem.slug == data["slug"],
        )
    )
    item = result.scalar_one_or_none()
    fields = {
        "title": data["title"],
        "item_type": data.get("item_type", "study_plan"),
        "status": data.get("status", "planned"),
        "sort_order": data.get("sort_order", sort_order),
        "notes": data.get("summary") or data.get("notes"),
        "provider": data.get("provider"),
        "url": data.get("url"),
    }
    if item is None:
        item = LearningItem(user_id=user_id, track_id=track.id, slug=data["slug"], progress=0, **fields)
        db.add(item)
        await db.flush()
    else:
        for k, v in fields.items():
            setattr(item, k, v)
        await db.flush()
    return item


async def _upsert_concept(
    db: AsyncSession, user_id: str, item: LearningItem, data: dict, sort_order: int
) -> LearningConcept:
    from sqlalchemy import select

    result = await db.execute(
        select(LearningConcept).where(
            LearningConcept.user_id == user_id,
            LearningConcept.item_id == item.id,
            LearningConcept.slug == data["slug"],
        )
    )
    concept = result.scalar_one_or_none()
    fields = {
        "title": data["title"],
        "summary": data.get("summary"),
        "week_number": data.get("week_number"),
        "estimated_minutes": data.get("estimated_minutes"),
        "sort_order": data.get("sort_order", sort_order),
    }
    if concept is None:
        concept = LearningConcept(
            user_id=user_id,
            item_id=item.id,
            slug=data["slug"],
            confidence=0,
            can_explain=False,
            failure_modes_known=False,
            tradeoffs_known=False,
            **fields,
        )
        db.add(concept)
        await db.flush()
    else:
        for k, v in fields.items():
            if k not in PROGRESS_FIELDS_CONCEPT:
                setattr(concept, k, v)
        await db.flush()
    return concept


async def _upsert_resource(
    db: AsyncSession,
    user_id: str,
    data: dict,
    sort_order: int,
    *,
    item_id: str | None,
    concept_id: str | None,
) -> LearningResource:
    from sqlalchemy import select

    q = select(LearningResource).where(
        LearningResource.user_id == user_id, LearningResource.url == data["url"]
    )
    if concept_id:
        q = q.where(LearningResource.concept_id == concept_id)
    else:
        q = q.where(LearningResource.item_id == item_id, LearningResource.concept_id.is_(None))
    result = await db.execute(q)
    resource = result.scalar_one_or_none()
    fields = {
        "resource_type": data.get("resource_type", "article"),
        "title": data["title"],
        "url": data["url"],
        "provider": data.get("provider"),
        "author": data.get("author"),
        "duration_minutes": data.get("duration_minutes"),
        "priority": data.get("priority", "supporting"),
        "sort_order": data.get("sort_order", sort_order),
        "last_verified_at": _parse_date(data.get("last_verified_at")),
        "item_id": item_id,
        "concept_id": concept_id,
    }
    if resource is None:
        resource = LearningResource(user_id=user_id, is_consumed=False, **fields)
        db.add(resource)
        await db.flush()
    else:
        for k, v in fields.items():
            if k not in PROGRESS_FIELDS_RESOURCE:
                setattr(resource, k, v)
        await db.flush()
    return resource


async def _cli_main(slug: str, user_email: str) -> None:
    from sqlalchemy import select

    from app.core.database import async_session_factory
    from app.modules.auth.models import User

    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.email == user_email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"User not found: {user_email}", file=sys.stderr)
            sys.exit(1)
        track = await seed_track(db, user.id, slug)
        await db.commit()
        print(f"Seeded track {track.slug} ({track.id}) for {user_email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed a learning track from JSON")
    parser.add_argument("slug", help="Seed file slug (e.g. ai-systems-engineering)")
    parser.add_argument("--email", required=True, help="User email to own the track")
    args = parser.parse_args()
    asyncio.run(_cli_main(args.slug, args.email))


if __name__ == "__main__":
    main()
