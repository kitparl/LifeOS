"""Mastery model (PRD §30).

0=not_started 1=introduced 2=familiar 3=practicing 4=strong 5=mastered.

Deliberately simple and isolated so it can be replaced with a real spaced-repetition
algorithm later without touching callers — `UserVocabulary` already carries the
`next_review_at`/`review_interval`/`repetition_count`/`ease_factor` columns a future
SR algorithm would need (PRD §30 "prepare the data model for").
"""

from __future__ import annotations

MIN_MASTERY = 0
MAX_MASTERY = 5


def next_mastery_level(current: int, is_correct: bool) -> int:
    delta = 1 if is_correct else -1
    return max(MIN_MASTERY, min(MAX_MASTERY, current + delta))
