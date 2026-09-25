"""UI news categories mapped to documented FreeNewsAPI `/v1/search` parameters.

FreeNewsAPI's search has no category filter and its per-article `categories` tags are unreliable,
so each category is a search phrase or a country filter. Every mapping was checked against the
live API (2026-09-25) to return current results. This is the single source of the mapping; the
frontend lists categories via `GET /news/categories`.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NewsCategoryDef:
    id: str
    label: str
    params: dict[str, str] = field(default_factory=dict)


CATEGORIES: tuple[NewsCategoryDef, ...] = (
    NewsCategoryDef("all", "All"),
    NewsCategoryDef("ai", "AI", {"q": "artificial intelligence"}),
    NewsCategoryDef("technology", "Technology", {"q": "technology"}),
    NewsCategoryDef("business", "Business", {"q": "business"}),
    NewsCategoryDef("finance", "Finance", {"q": "finance"}),
    NewsCategoryDef("science", "Science", {"q": "science"}),
    NewsCategoryDef("health", "Health", {"q": "health"}),
    NewsCategoryDef("sports", "Sports", {"q": "sports"}),
    NewsCategoryDef("entertainment", "Entertainment", {"q": "entertainment"}),
    NewsCategoryDef("world", "World", {"q": "international"}),
    NewsCategoryDef("india", "India", {"country": "IN"}),
    NewsCategoryDef("politics", "Politics", {"q": "politics"}),
    NewsCategoryDef("climate", "Climate", {"q": "climate change"}),
    NewsCategoryDef("startups", "Startups", {"q": "startups"}),
)

_BY_ID: dict[str, NewsCategoryDef] = {c.id: c for c in CATEGORIES}
CATEGORY_IDS: frozenset[str] = frozenset(_BY_ID)


def resolve(category_id: str) -> dict[str, str]:
    """Vendor params for a category id. Raises KeyError for unknown ids (validated at the API)."""
    return dict(_BY_ID[category_id].params)
