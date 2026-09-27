"""Idempotent DSA catalog seeder: patterns + every catalog title (as drafts) + built content (published).

Usage (from backend/, never at app startup):
    python -m app.modules.dsa.seeder            # seed / update
    python -m app.modules.dsa.seeder --force    # also overwrite problems edited in the admin UI

Upsert by slug. A problem edited in the admin UI (`edited_in_ui`) is left alone unless --force;
a problem whose built content is unchanged (`content_hash`) is skipped. Seed files are validated
before anything is written.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.dsa.content.build import SEEDS_DIR, load_catalog
from app.modules.dsa.judge.signature import SignatureError, parse_spec, validate_expected, validate_input
from app.modules.dsa.models import DsaPattern, DsaProblem, DsaTestCase
from app.modules.dsa.repository import CatalogRepository


class SeedValidationError(ValueError):
    pass


@dataclass
class SeedReport:
    patterns: int = 0
    drafts_created: int = 0
    published: int = 0
    unchanged: int = 0
    skipped_edited: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [
            f"patterns: {self.patterns}",
            f"draft problems created: {self.drafts_created}",
            f"problems published/updated: {self.published}",
            f"unchanged: {self.unchanged}",
        ]
        if self.skipped_edited:
            lines.append("skipped (edited in UI; use --force): " + ", ".join(self.skipped_edited))
        return "\n".join(lines)


def content_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def load_content(seeds_dir: Path) -> dict[str, dict[str, Any]]:
    """{slug: built problem payload} from every pNN-*.json, validated."""
    content: dict[str, dict[str, Any]] = {}
    for path in sorted(seeds_dir.glob("p[0-9][0-9]-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for problem in data.get("problems", []):
            _validate(problem, path.name)
            content[problem["slug"]] = problem
    return content


def _validate(problem: dict[str, Any], source: str) -> None:
    where = f"{source}:{problem.get('slug')}"
    try:
        spec = parse_spec(problem["signature"])
        if not any(t["is_sample"] for t in problem["tests"]):
            raise SeedValidationError(f"{where}: no sample tests")
        for t in problem["tests"]:
            validate_input(spec, t["input"])
            validate_expected(spec, t["expected"], t["input"])
    except (KeyError, TypeError, SignatureError, ValueError) as exc:
        raise SeedValidationError(f"{where}: {exc}") from exc


async def seed(db: AsyncSession, *, force: bool = False, seeds_dir: Path = SEEDS_DIR) -> SeedReport:
    catalog = load_catalog(seeds_dir / "catalog.json")
    content = load_content(seeds_dir)
    unknown = set(content) - {p["slug"] for p in catalog["problems"]}
    if unknown:
        raise SeedValidationError(f"seed content for slugs not in the catalog: {sorted(unknown)}")

    report = SeedReport()
    pattern_ids = await _upsert_patterns(db, catalog["patterns"], report)
    existing = {p.slug: p for p in (await db.execute(select(DsaProblem))).scalars()}
    repo = CatalogRepository(db)
    for entry in catalog["problems"]:
        problem = existing.get(entry["slug"])
        if problem is None:
            problem = DsaProblem(slug=entry["slug"], status="draft")
            db.add(problem)
            report.drafts_created += 1
        elif problem.edited_in_ui and not force:
            if entry["slug"] in content:
                report.skipped_edited.append(entry["slug"])
            continue
        problem.pattern_id = pattern_ids[entry["pattern"]]
        problem.title = entry["title"]
        problem.difficulty = entry["difficulty"]
        problem.tags = entry["tags"]
        problem.display_order = entry["order"]
        payload = content.get(entry["slug"])
        if payload is None:
            continue
        digest = content_hash(payload)
        if problem.content_hash == digest and not problem.edited_in_ui:
            report.unchanged += 1
            continue
        await db.flush()
        _apply_content(problem, payload, digest)
        await repo.replace_tests(problem.id, _tests(problem.id, payload["tests"]))
        report.published += 1
    await db.flush()
    return report


async def _upsert_patterns(db: AsyncSession, patterns: list[dict[str, Any]], report: SeedReport) -> dict[int, str]:
    existing = {p.number: p for p in (await db.execute(select(DsaPattern))).scalars()}
    ids: dict[int, str] = {}
    for order, entry in enumerate(patterns):
        pattern = existing.get(entry["number"]) or DsaPattern(number=entry["number"])
        if pattern.id is None:
            db.add(pattern)
        pattern.slug = entry["slug"]
        pattern.name = entry["name"]
        pattern.description = entry["description"]
        pattern.week = entry["week"]
        pattern.display_order = order
        await db.flush()
        ids[entry["number"]] = pattern.id
        report.patterns += 1
    return ids


def _apply_content(problem: DsaProblem, payload: dict[str, Any], digest: str) -> None:
    problem.status = "published"
    problem.is_variant = payload["is_variant"]
    problem.statement = payload["statement"]
    problem.constraints = payload["constraints"]
    problem.signature = payload["signature"]
    problem.compare_mode = payload["compare_mode"]
    problem.checker = payload["checker"]
    problem.time_limit_ms = payload["time_limit_ms"]
    problem.memory_limit_mb = payload["memory_limit_mb"]
    problem.content_hash = digest
    problem.edited_in_ui = False
    problem.updated_by = None


def _tests(problem_id: str, tests: list[dict[str, Any]]) -> list[DsaTestCase]:
    return [
        DsaTestCase(
            problem_id=problem_id,
            position=i,
            input=t["input"],
            expected=t["expected"],
            is_sample=t["is_sample"],
            kind=t["kind"],
            explanation=t.get("explanation"),
        )
        for i, t in enumerate(tests)
    ]


async def run(force: bool) -> SeedReport:
    from app.core.database import async_session_factory, engine
    from app.core.schema_bootstrap import apply_schema

    await apply_schema()
    try:
        async with async_session_factory() as db:
            report = await seed(db, force=force)
            await db.commit()
    finally:
        await engine.dispose()
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed the DSA practice catalog (run from backend/)")
    parser.add_argument("--force", action="store_true", help="overwrite problems edited in the admin UI")
    args = parser.parse_args(argv)
    try:
        report = asyncio.run(run(args.force))
    except SeedValidationError as exc:
        print(f"seed rejected: {exc}", file=sys.stderr)
        return 1
    print(report.render())
    return 0


if __name__ == "__main__":
    sys.exit(main())
