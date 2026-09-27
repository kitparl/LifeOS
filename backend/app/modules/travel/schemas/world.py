from __future__ import annotations

from pydantic import BaseModel

from app.modules.travel.schemas.places import Marker


class WorldCounts(BaseModel):
    wishlist: int
    planned: int
    visited: int
    favourite: int
    trips: int
    completed_trips: int
    adventures: int
    photos: int


class WorldOverview(BaseModel):
    """The lifetime travel map (spec §20): every layer's markers plus the totals."""

    markers: list[Marker]
    counts: WorldCounts
