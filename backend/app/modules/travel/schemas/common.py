"""Bounded field types shared by every Travel schema (SECURITY-05)."""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator, Field

_URL_RE = re.compile(r"^https?://[^\s<>\"']{1,490}$", re.IGNORECASE)


def _strip_required(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("must not be blank")
    return value


def _strip_optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _check_optional_links(values: list[str] | None) -> list[str] | None:
    return None if values is None else _check_links(values)


def _check_links(values: list[str]) -> list[str]:
    cleaned = [v.strip() for v in values if v.strip()]
    for url in cleaned:
        if not _URL_RE.match(url):
            raise ValueError("links must be http(s) URLs")
    return cleaned


Lat = Annotated[float, Field(ge=-90, le=90)]
Lng = Annotated[float, Field(ge=-180, le=180)]
Name = Annotated[str, Field(min_length=1, max_length=200), AfterValidator(_strip_required)]
OptText200 = Annotated[str | None, Field(default=None, max_length=200), AfterValidator(_strip_optional)]
OptText300 = Annotated[str | None, Field(default=None, max_length=300), AfterValidator(_strip_optional)]
OptText120 = Annotated[str | None, Field(default=None, max_length=120), AfterValidator(_strip_optional)]
OptText80 = Annotated[str | None, Field(default=None, max_length=80), AfterValidator(_strip_optional)]
Notes = Annotated[str | None, Field(default=None, max_length=10_000)]
Links = Annotated[list[str], Field(default_factory=list, max_length=20), AfterValidator(_check_links)]
OptLinks = Annotated[list[str] | None, Field(default=None, max_length=20), AfterValidator(_check_optional_links)]
EntityId = Annotated[str, Field(min_length=1, max_length=36, pattern=r"^[A-Za-z0-9-]+$")]
TagName = Annotated[str, Field(min_length=1, max_length=32), AfterValidator(_strip_required)]
