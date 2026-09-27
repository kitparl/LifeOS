"""Content build (reference-generated expected outputs), seeder idempotency / UI-edit protection, CLI."""

import json
import os

import pytest
from app.modules.auth.models import User
from app.modules.dsa import cli as dsa_cli
from app.modules.dsa.content import build
from app.modules.dsa.content.build import ContentError, PatternSource, build_pattern, discover_sources, render
from app.modules.dsa.content.model import Example, ProblemSource, function, ints
from app.modules.dsa.models import DsaPattern, DsaProblem, DsaTestCase
from app.modules.dsa.seeder import SeedValidationError, seed
from sqlalchemy import func, select

CATALOG = {
    "patterns": [
        {"number": 1, "slug": "two-pointers", "name": "Two Pointers", "week": 1, "description": "Two indices."}
    ],
    "problems": [
        {"pattern": 1, "slug": "pair-sum", "title": "Pair Sum", "difficulty": "easy", "tags": ["blind75"], "order": 0},
        {"pattern": 1, "slug": "later-problem", "title": "Later Problem", "difficulty": "hard", "tags": [], "order": 1},
    ],
}


def _pair_sum(nums: list[int], target: int) -> bool:
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        s = nums[lo] + nums[hi]
        if s == target:
            return True
        lo, hi = (lo + 1, hi) if s < target else (lo, hi - 1)
    return False


def _source(**overrides) -> ProblemSource:
    fields = dict(
        title="Pair Sum",
        statement="Given a sorted array `nums`, decide whether two different elements add up to `target`.",
        constraints="- `0 <= nums.length <= 1000`",
        signature=function("pairSum", [("nums", "int[]"), ("target", "int")], "bool"),
        reference=_pair_sum,
        examples=[Example([[1, 2, 4], 6], "2 + 4 = 6."), Example([[1, 2], 5])],
        edge_cases=[[[], 0], [[5], 10], [[1, 2, 4], 6]],  # the last duplicates an example and is dropped
        generator=lambda rng: [sorted(ints(rng, rng.randint(0, 20), -50, 50)), rng.randint(-100, 100)],
        random_count=5,
    )
    fields.update(overrides)
    return ProblemSource(**fields)


def _pattern(*problems: ProblemSource) -> PatternSource:
    return PatternSource(1, list(problems) or [_source()], "test")


# ---------------------------------------------------------------- build


def test_build_generates_expected_from_reference():
    seed_data = build_pattern(_pattern(), CATALOG)
    (problem,) = seed_data["problems"]
    assert problem["slug"] == "pair-sum"
    kinds = [t["kind"] for t in problem["tests"]]
    assert kinds[:2] == ["example", "example"] and kinds.count("edge") == 2 and kinds.count("random") <= 5
    for t in problem["tests"]:
        assert t["expected"] == _pair_sum(*t["input"])
    assert problem["tests"][0]["explanation"] == "2 + 4 = 6." and problem["tests"][0]["is_sample"]


def test_build_is_deterministic():
    assert render(build_pattern(_pattern(), CATALOG)) == render(build_pattern(_pattern(), CATALOG))


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"title": "Unknown"}, "not a catalog title"),
        ({"examples": [Example([[1], 1])]}, "2-3 examples"),
        ({"reference": lambda nums, target: 1 / 0}, "reference failed"),
        ({"reference": lambda nums, target: "yes"}, "output invalid"),
        ({"edge_cases": [[[1], "x"]]}, "bad input"),
        ({"compare": "fuzzy"}, "unknown compare mode"),
        ({"compare": "checker", "checker": "nope"}, "unknown checker"),
        ({"signature": function("f", [("x", "set")], "int")}, "invalid signature"),
        ({"random_count": 50}, "max 40"),
    ],
)
def test_build_rejects_bad_sources(overrides, message):
    with pytest.raises(ContentError, match=message):
        build_pattern(_pattern(_source(**overrides)), CATALOG)


def test_build_cross_checks_brute():
    build_pattern(
        _pattern(
            _source(
                brute=lambda nums, target: any(
                    nums[i] + nums[j] == target for i in range(len(nums)) for j in range(i + 1, len(nums))
                )
            )
        ),
        CATALOG,
    )
    with pytest.raises(ContentError, match="reference and brute disagree"):
        build_pattern(_pattern(_source(brute=lambda nums, target: False)), CATALOG)


def test_build_rejects_nondeterministic_reference():
    calls = iter(range(1000))
    with pytest.raises(ContentError, match="not deterministic"):
        build_pattern(_pattern(_source(reference=lambda nums, target: next(calls) % 2 == 0)), CATALOG)


def test_committed_seeds_match_the_catalog():
    """Cheap check (always runs): every seed file names catalog problems of its own pattern."""
    catalog = build.load_catalog()
    assert len(catalog["patterns"]) == 29 and len(catalog["problems"]) == 656
    owner = {p["slug"]: p["pattern"] for p in catalog["problems"]}
    for path in build.SEEDS_DIR.glob("p[0-9][0-9]-*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert path.name == build.seed_path(data["pattern"], catalog).name
        assert all(owner[p["slug"]] == data["pattern"] for p in data["problems"])


@pytest.mark.skipif(os.environ.get("DSA_CONTENT_E2E") != "1", reason="full rebuild; set DSA_CONTENT_E2E=1")
def test_real_sources_rebuild_to_committed_seeds():
    """Every source builds and matches its committed seed file (same as `content.build --check`)."""
    catalog = build.load_catalog()
    for pattern in discover_sources():
        path = build.seed_path(pattern.number, catalog)
        assert path.exists(), f"run: python -m app.modules.dsa.content.build --pattern {pattern.number}"
        assert path.read_text(encoding="utf-8") == render(build_pattern(pattern, catalog))


# ---------------------------------------------------------------- seeder


def _write_seeds(tmp_path, pattern_seed=None):
    (tmp_path / "catalog.json").write_text(json.dumps(CATALOG))
    if pattern_seed is not None:
        (tmp_path / "p01-two-pointers.json").write_text(render(pattern_seed))
    return tmp_path


async def _count(db, model) -> int:
    return (await db.execute(select(func.count()).select_from(model))).scalar_one()


async def test_seed_creates_drafts_and_published(client, tmp_path):
    seeds = _write_seeds(tmp_path, build_pattern(_pattern(), CATALOG))
    async with client.session_factory() as db:
        report = await seed(db, seeds_dir=seeds)
        await db.commit()
        assert (report.patterns, report.drafts_created, report.published) == (1, 2, 1)
        problems = {p.slug: p for p in (await db.execute(select(DsaProblem))).scalars()}
        assert problems["pair-sum"].status == "published" and problems["pair-sum"].tags == ["blind75"]
        assert problems["later-problem"].status == "draft" and problems["later-problem"].signature is None
        n_tests = await _count(db, DsaTestCase)
        assert n_tests == len(build_pattern(_pattern(), CATALOG)["problems"][0]["tests"])

        again = await seed(db, seeds_dir=seeds)
        await db.commit()
        assert (again.drafts_created, again.published, again.unchanged) == (0, 0, 1)
        assert await _count(db, DsaTestCase) == n_tests
        assert await _count(db, DsaPattern) == 1


async def test_seed_protects_ui_edits_unless_forced(client, tmp_path):
    seeds = _write_seeds(tmp_path, build_pattern(_pattern(), CATALOG))
    async with client.session_factory() as db:
        await seed(db, seeds_dir=seeds)
        problem = (await db.execute(select(DsaProblem).where(DsaProblem.slug == "pair-sum"))).scalar_one()
        problem.statement = "edited by admin"
        problem.edited_in_ui = True
        await db.commit()

        changed = build_pattern(_pattern(_source(statement="A new original statement.")), CATALOG)
        _write_seeds(tmp_path, changed)
        report = await seed(db, seeds_dir=seeds)
        await db.commit()
        assert report.skipped_edited == ["pair-sum"]
        await db.refresh(problem)
        assert problem.statement == "edited by admin"

        forced = await seed(db, force=True, seeds_dir=seeds)
        await db.commit()
        await db.refresh(problem)
        assert forced.published == 1 and problem.statement.startswith("A new original") and not problem.edited_in_ui


async def test_seed_rejects_invalid_files(client, tmp_path):
    seed_data = build_pattern(_pattern(), CATALOG)
    seed_data["problems"][0]["tests"][0]["expected"] = "not a bool"
    seeds = _write_seeds(tmp_path, seed_data)
    async with client.session_factory() as db:
        with pytest.raises(SeedValidationError):
            await seed(db, seeds_dir=seeds)


# ---------------------------------------------------------------- cli


async def test_grant_and_revoke_admin(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "dsa_admin",
            "email": "dsa-admin@example.com",
            "password": "password123",
            "display_name": "A",
        },
    )
    async with client.session_factory() as db:
        await dsa_cli.set_admin(db, "DSA_Admin", True)
        await db.commit()
        user = (await db.execute(select(User).where(User.username == "dsa_admin"))).scalar_one()
        assert user.is_admin
        await dsa_cli.set_admin(db, "dsa_admin", False)
        await db.commit()
        await db.refresh(user)
        assert not user.is_admin
        with pytest.raises(dsa_cli.UserNotFoundError):
            await dsa_cli.set_admin(db, "nobody", True)
