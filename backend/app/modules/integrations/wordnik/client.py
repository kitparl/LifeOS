"""Thin Wordnik v4 client. Server-side only; the key never reaches the browser or a URL.

The key is sent in the `api_key` header (Wordnik's gateway accepts it there as well as in the
query string), so it cannot leak through request-URL logging. Every response's hourly
rate-limit headers are captured in `last_usage` for the Word Lab's "usage remaining" display.

Error `code` values match the AI adapters' (`ai/adapters/base.py`) so the frontend handles
vendor failures uniformly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx

from app.core.text import clean_text
from app.modules.integrations.wordnik.config import WordnikUsage

BASE_URL = "https://api.wordnik.com/v4"
TIMEOUT_SECONDS = 10.0
_LABEL = "Wordnik"


class WordnikError(Exception):
    """Base error for every Wordnik call. `code` is a stable, client-facing identifier."""

    code: str = "provider_unavailable"


class WordnikMissingCredentialError(WordnikError):
    code = "missing_credential"


class WordnikInvalidCredentialError(WordnikError):
    code = "invalid_credential"


class WordnikRateLimitError(WordnikError):
    code = "rate_limit"


class WordnikTimeoutError(WordnikError):
    code = "timeout"


class WordnikUnavailableError(WordnikError):
    code = "provider_unavailable"


class WordnikMalformedResponseError(WordnikError):
    code = "malformed_response"


@dataclass(frozen=True)
class Definition:
    part_of_speech: str | None
    text: str


@dataclass(frozen=True)
class ReverseMatch:
    word: str
    hint: str | None


@dataclass(frozen=True)
class WordOfTheDayEntry:
    word: str
    definitions: list[Definition]
    examples: list[str]
    note: str | None


def _http_client(timeout: float) -> httpx.AsyncClient:
    """Single construction point for Wordnik HTTP clients (tests patch this seam)."""
    return httpx.AsyncClient(timeout=timeout)


def _header_int(headers: httpx.Headers, name: str) -> int | None:
    raw = headers.get(name)
    try:
        return int(raw) if raw is not None else None
    except ValueError:
        return None


def _usage_from_headers(headers: httpx.Headers) -> WordnikUsage | None:
    remaining = _header_int(headers, "x-ratelimit-remaining-hour")
    limit = _header_int(headers, "x-ratelimit-limit-hour")
    if remaining is None or limit is None:
        return None
    return WordnikUsage(remaining=remaining, limit=limit, observed_at=datetime.now(timezone.utc))


def _definitions(raw: Any) -> list[Definition]:
    if not isinstance(raw, list):
        return []
    out: list[Definition] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        text = clean_text(item.get("text"))
        if text:
            pos = clean_text(item.get("partOfSpeech")) or None
            out.append(Definition(part_of_speech=pos, text=text))
    return out


def _words(raw: Any) -> list[str]:
    """`word` values from a list of {"word": ...} objects, deduped in order."""
    if not isinstance(raw, list):
        return []
    seen: dict[str, None] = {}
    for item in raw:
        word = clean_text(item.get("word")) if isinstance(item, dict) else ""
        if word:
            seen.setdefault(word, None)
    return list(seen)


class WordnikClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise WordnikMissingCredentialError("Connect a Wordnik API key in Integrations first.")
        self._api_key = api_key
        self.last_usage: WordnikUsage | None = None

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """GET a Wordnik path. Returns decoded JSON, or None when Wordnik has no entry (404)."""
        try:
            async with _http_client(TIMEOUT_SECONDS) as client:
                res = await client.get(f"{BASE_URL}{path}", params=params, headers={"api_key": self._api_key})
        except httpx.TimeoutException as exc:
            raise WordnikTimeoutError(f"{_LABEL} request timed out.") from exc
        except httpx.HTTPError as exc:
            raise WordnikUnavailableError(f"{_LABEL} is temporarily unavailable.") from exc

        self.last_usage = _usage_from_headers(res.headers) or self.last_usage
        if res.status_code in (401, 403):
            raise WordnikInvalidCredentialError(f"Invalid or revoked {_LABEL} API key. Check Integrations.")
        if res.status_code == 429:
            raise WordnikRateLimitError(f"{_LABEL} hourly limit reached. Try again later.")
        if res.status_code == 404:
            return None
        if res.status_code >= 400:
            raise WordnikUnavailableError(f"{_LABEL} could not complete the request (HTTP {res.status_code}).")
        try:
            return res.json()
        except ValueError as exc:
            raise WordnikMalformedResponseError(f"{_LABEL} returned a non-JSON response.") from exc

    @staticmethod
    def _word_path(word: str, endpoint: str) -> str:
        return f"/word.json/{quote(word, safe='')}/{endpoint}"

    async def word_of_the_day(self, day: date) -> WordOfTheDayEntry | None:
        data = await self._get("/words.json/wordOfTheDay", {"date": day.isoformat()})
        if data is None:
            return None
        if not isinstance(data, dict):
            raise WordnikMalformedResponseError(f"{_LABEL} returned an unexpected Word of the Day.")
        word = clean_text(data.get("word"))
        if not word:
            return None
        raw_examples = data.get("examples")
        examples = [clean_text(e.get("text")) for e in raw_examples or [] if isinstance(e, dict)]
        return WordOfTheDayEntry(
            word=word,
            definitions=_definitions(data.get("definitions")),
            examples=[e for e in examples if e],
            note=clean_text(data.get("note")) or None,
        )

    async def definitions(self, word: str, limit: int = 5) -> list[Definition]:
        data = await self._get(self._word_path(word, "definitions"), {"limit": limit, "useCanonical": "true"})
        return _definitions(data)

    async def top_example(self, word: str) -> str | None:
        data = await self._get(self._word_path(word, "topExample"), {"useCanonical": "true"})
        return (clean_text(data.get("text")) or None) if isinstance(data, dict) else None

    async def related_words(self, word: str, relationship: str, limit: int = 30) -> list[str]:
        data = await self._get(
            self._word_path(word, "relatedWords"),
            {"useCanonical": "true", "relationshipTypes": relationship, "limitPerRelationshipType": limit},
        )
        if not isinstance(data, list):
            return []
        words: dict[str, None] = {}
        for group in data:
            if isinstance(group, dict) and group.get("relationshipType") == relationship:
                for w in group.get("words") or []:
                    text = clean_text(w)
                    if text:
                        words.setdefault(text, None)
        return list(words)

    async def reverse_dictionary(self, query: str, limit: int = 20) -> list[ReverseMatch]:
        data = await self._get("/words.json/reverseDictionary", {"query": query, "limit": limit})
        results = data.get("results") if isinstance(data, dict) else None
        if not isinstance(results, list):
            return []
        out: list[ReverseMatch] = []
        seen: set[str] = set()
        for item in results:
            if not isinstance(item, dict):
                continue
            word = clean_text(item.get("word"))
            if word and word not in seen:
                seen.add(word)
                out.append(ReverseMatch(word=word, hint=clean_text(item.get("text")) or None))
        return out

    async def random_words(self, limit: int) -> list[str]:
        data = await self._get(
            "/words.json/randomWords",
            {"hasDictionaryDef": "true", "limit": limit, "minCorpusCount": 1000, "minLength": 4, "maxLength": 12},
        )
        return _words(data)

    async def random_word(self) -> str | None:
        data = await self._get(
            "/words.json/randomWord",
            {"hasDictionaryDef": "true", "minCorpusCount": 1000, "minLength": 4, "maxLength": 10},
        )
        return (clean_text(data.get("word")) or None) if isinstance(data, dict) else None
