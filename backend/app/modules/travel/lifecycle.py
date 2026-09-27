"""Pure trip lifecycle rules: drafts, confirmation and completion (requirements D-12, spec §21)."""

from __future__ import annotations

# Allowed manual status moves. Confirm (draft -> planning), back-to-draft and complete have their own endpoints
# but are validated here too, so there is one table to read.
TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"planning"}),
    "planning": frozenset({"draft", "booked", "active", "completed"}),
    "booked": frozenset({"draft", "planning", "active", "completed"}),
    "active": frozenset({"completed"}),
    "completed": frozenset(),
}


def can_transition(current: str, target: str) -> bool:
    return target in TRANSITIONS.get(current, frozenset())


def promoted_status(place_status: str) -> str | None:
    """Confirming a trip plans its wishlist places; anything else is already further along."""
    return "planned" if place_status == "wishlist" else None


def reverted_status(place_status: str, promoted_by_trip: bool) -> str | None:
    """Back to draft undoes only this trip's own promotion, and only if nothing moved the place on since."""
    return "wishlist" if promoted_by_trip and place_status == "planned" else None


def visited_status(place_status: str) -> str | None:
    """Completing a trip marks places visited, but never downgrades a favourite."""
    return None if place_status in ("visited", "favourite") else "visited"
