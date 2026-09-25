"""Word Lab (Wordnik-backed lookups, practice games, Save as vocabulary) and Word of the Day.

Rows created here live in the shared `vocabulary` table with `exclude_from_daily=True` and a
reserved sequence band, so the daily allocator (sequencing.allocate_next) never hands them out.
The Wordnik key is per user (Integrations); the Word of the Day row is app-wide, fetched at most
once per IST date and then served from the DB.
"""

from __future__ import annotations

import logging
import random
from collections.abc import Awaitable, Callable
from datetime import date
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AppError,
    BadGatewayError,
    BadRequestError,
    ConflictError,
    ServiceUnavailableError,
    UnprocessableError,
)
from app.core.timezone import ist_today
from app.modules.auth.models import User
from app.modules.communication.vocabulary.models import (
    SOURCE_API,
    SOURCE_USER_SAVED,
    Vocabulary,
)
from app.modules.communication.vocabulary.repository import VocabularyRepository
from app.modules.communication.vocabulary.schemas import (
    VocabularyDetail,
    WordLabDefinition,
    WordLabGameResponse,
    WordLabGameType,
    WordLabLookupResponse,
    WordLabMode,
    WordLabSaveRequest,
    WordLabSaveResponse,
    WordLabStatus,
    WordLabWord,
    WordOfTheDayResponse,
)
from app.modules.communication.vocabulary.wordnik_mapper import (
    new_saved_id,
    normalize_term,
    vocabulary_fields,
    word_of_the_day_fields,
    word_of_the_day_id,
)
from app.modules.integrations.wordnik.client import (
    WordnikClient,
    WordnikError,
    WordnikInvalidCredentialError,
    WordnikMalformedResponseError,
    WordnikMissingCredentialError,
    WordnikRateLimitError,
    WordnikUsage,
)
from app.modules.integrations.wordnik.service import WordnikIntegrationService

logger = logging.getLogger(__name__)

_RELATIONSHIP_BY_MODE = {"synonyms": "synonym", "rhymes": "rhyme"}
GAME_OPTION_COUNT = 4
_GAME_DEFINITION_MAX_CHARS = 240


def _to_app_error(exc: WordnikError) -> AppError:
    """Map a Wordnik error to the {"code", "message"} detail shape used for vendor errors.

    Credential problems are 400, not 401: the frontend treats 401 as an expired session and
    refreshes + retries, which would spend a second vendor call on a key that cannot work.
    """
    detail = {"code": exc.code, "message": str(exc)}
    if isinstance(exc, (WordnikMissingCredentialError, WordnikInvalidCredentialError)):
        return BadRequestError(detail)
    if isinstance(exc, WordnikMalformedResponseError):
        return BadGatewayError(detail)
    return ServiceUnavailableError(detail)


def _scramble(word: str) -> str:
    letters = list(word)
    for _ in range(10):
        random.shuffle(letters)
        if "".join(letters) != word:
            break
    return "".join(letters)


def _short(text: str) -> str:
    if len(text) <= _GAME_DEFINITION_MAX_CHARS:
        return text
    return text[: _GAME_DEFINITION_MAX_CHARS - 1].rstrip() + "…"


class WordLabService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = VocabularyRepository(db)
        self.wordnik = WordnikIntegrationService(db)

    async def _client(self, user: User) -> WordnikClient:
        client = await self.wordnik.client_for(user.id)
        if client is None:
            raise _to_app_error(WordnikMissingCredentialError("Connect a Wordnik API key in Integrations first."))
        return client

    async def _fail(self, user: User, client: WordnikClient, exc: WordnikError) -> AppError:
        """Persist the latest quota reading, then return the error to raise.

        The request transaction rolls back when the error propagates, so the usage write is
        committed here; it is the only pending change on a failed lookup.
        """
        usage = client.last_usage
        if isinstance(exc, WordnikRateLimitError) and usage is not None:
            usage = WordnikUsage(remaining=0, limit=usage.limit, observed_at=usage.observed_at)
        await self.wordnik.record_usage(user.id, usage)
        await self.db.commit()
        return _to_app_error(exc)

    # ------------------------------------------------------------------
    # Status / lookup
    # ------------------------------------------------------------------

    async def status(self, user: User) -> WordLabStatus:
        connected = await self.wordnik.client_for(user.id) is not None
        pct = await self.wordnik.usage_pct(user.id) if connected else None
        return WordLabStatus(connected=connected, usage_remaining_pct=pct)

    async def lookup(self, user: User, q: str, mode: WordLabMode) -> WordLabLookupResponse:
        query = q.strip()
        if not query:
            raise BadRequestError("Enter a word to look up")
        client = await self._client(user)
        result = WordLabLookupResponse(mode=mode, query=query)
        try:
            if mode == "dictionary":
                definitions = await client.definitions(query)
                result.definitions = [
                    WordLabDefinition(part_of_speech=d.part_of_speech, text=d.text) for d in definitions
                ]
                if definitions:
                    result.example = await client.top_example(query)
            elif mode == "explorer":
                matches = await client.reverse_dictionary(query)
                result.words = [WordLabWord(word=m.word, hint=m.hint) for m in matches]
            else:
                words = await client.related_words(query, _RELATIONSHIP_BY_MODE[mode])
                result.words = [WordLabWord(word=w) for w in words]
        except WordnikError as exc:
            raise await self._fail(user, client, exc) from exc
        result.usage_remaining_pct = await self.wordnik.record_usage(user.id, client.last_usage)
        return result

    # ------------------------------------------------------------------
    # Practice games (stateless; nothing is persisted)
    # ------------------------------------------------------------------

    async def game(self, user: User, game_type: WordLabGameType) -> WordLabGameResponse:
        client = await self._client(user)
        builders: dict[str, Callable[[WordnikClient], Awaitable[WordLabGameResponse | None]]] = {
            "guess_word": self._guess_word,
            "guess_meaning": self._guess_meaning,
            "scramble": self._scramble_round,
        }
        try:
            # Random words occasionally lack a usable definition; one retry keeps quota use bounded.
            round_ = await builders[game_type](client) or await builders[game_type](client)
        except WordnikError as exc:
            raise await self._fail(user, client, exc) from exc
        pct = await self.wordnik.record_usage(user.id, client.last_usage)
        if round_ is None:
            raise ServiceUnavailableError(
                {"code": "provider_unavailable", "message": "Could not build a round right now. Try again."}
            )
        round_.usage_remaining_pct = pct
        return round_

    async def _guess_word(self, client: WordnikClient) -> WordLabGameResponse | None:
        words = await client.random_words(GAME_OPTION_COUNT)
        if len(words) < 2:
            return None
        answer_index = random.randrange(len(words))
        definitions = await client.definitions(words[answer_index], limit=1)
        if not definitions:
            return None
        return WordLabGameResponse(
            type="guess_word", prompt=_short(definitions[0].text), options=words, answer_index=answer_index
        )

    async def _guess_meaning(self, client: WordnikClient) -> WordLabGameResponse | None:
        words = await client.random_words(GAME_OPTION_COUNT)
        pairs: list[tuple[str, str]] = []
        for word in words:
            definitions = await client.definitions(word, limit=1)
            if definitions:
                pairs.append((word, _short(definitions[0].text)))
        if len(pairs) < 2:
            return None
        answer_index = random.randrange(len(pairs))
        return WordLabGameResponse(
            type="guess_meaning",
            prompt=pairs[answer_index][0],
            options=[meaning for _, meaning in pairs],
            answer_index=answer_index,
        )

    async def _scramble_round(self, client: WordnikClient) -> WordLabGameResponse | None:
        word = await client.random_word()
        if not word:
            return None
        definitions = await client.definitions(word, limit=1)
        if not definitions:
            return None
        return WordLabGameResponse(
            type="scramble", prompt=_scramble(word.lower()), answer=word.lower(), hint=_short(definitions[0].text)
        )

    # ------------------------------------------------------------------
    # Save as vocabulary
    # ------------------------------------------------------------------

    async def save(self, user: User, data: WordLabSaveRequest) -> WordLabSaveResponse:
        await self._client(user)  # Word Lab tools are locked until Wordnik is connected.
        fields = vocabulary_fields(
            term=data.term,
            definition=data.definition,
            part_of_speech=data.part_of_speech,
            example=data.example,
            synonyms=data.synonyms,
        )
        if not fields["term"] or not fields["simple_meaning"]:
            raise UnprocessableError("A word and its meaning are required")
        row = await self.repo.find_by_normalized_term(normalize_term(fields["term"]))
        created = row is None
        if row is None:
            try:
                async with self.db.begin_nested():
                    row = await self._insert(fields, row_id=new_saved_id(), source=SOURCE_USER_SAVED)
            except IntegrityError as exc:
                raise ConflictError("Saving collided with another save — please retry") from exc
        # Vocabulary rows are shared, so the per-user record of "I saved this" is a bookmark.
        # It also covers words that already existed (e.g. seeded ones), which get no new row.
        if await self.repo.get_bookmark(user.id, row.id) is None:
            self.repo.new_bookmark(user.id, row.id)
            await self.db.flush()
        return WordLabSaveResponse(id=row.id, created=created)

    async def _insert(
        self, fields: dict[str, Any], *, row_id: str, source: str, wotd_for_date: date | None = None
    ) -> Vocabulary:
        collection = await self.repo.get_default_collection()
        if collection is None:
            raise ServiceUnavailableError("The vocabulary dataset has not been imported yet")
        row = Vocabulary(
            id=row_id,
            collection_id=collection.id,
            sequence_number=await self.repo.next_reserved_sequence_number(),
            source=source,
            exclude_from_daily=True,
            wotd_for_date=wotd_for_date,
            **fields,
        )
        self.db.add(row)
        await self.db.flush()
        return row

    # ------------------------------------------------------------------
    # Word of the Day
    # ------------------------------------------------------------------

    async def word_of_the_day(self, user: User) -> WordOfTheDayResponse:
        today = ist_today()
        client = await self.wordnik.client_for(user.id)
        if client is None:
            return WordOfTheDayResponse(connected=False, date=today)
        row = await self.repo.get_word_of_the_day(today)
        if row is None:
            row = await self._fetch_word_of_the_day(user, client)
        vocabulary = VocabularyDetail.model_validate(row) if row is not None else None
        return WordOfTheDayResponse(connected=True, date=today, vocabulary=vocabulary)

    async def _fetch_word_of_the_day(self, user: User, client: WordnikClient) -> Vocabulary | None:
        """One vendor call, then store on `vocabulary` (reusing an existing row for the same term)."""
        today = ist_today()
        try:
            entry = await client.word_of_the_day(today)
        except WordnikError as exc:
            logger.warning("Word of the Day fetch failed (%s)", exc.code)
            await self.wordnik.record_usage(user.id, client.last_usage)
            return None
        await self.wordnik.record_usage(user.id, client.last_usage)
        fields = word_of_the_day_fields(entry) if entry is not None else None
        if fields is None:
            logger.warning("Word of the Day for %s had no usable definition", today)
            return None
        try:
            async with self.db.begin_nested():
                row = await self.repo.find_by_normalized_term(normalize_term(fields["term"]))
                if row is not None:
                    row.wotd_for_date = today
                    await self.db.flush()
                else:
                    row = await self._insert(
                        fields, row_id=word_of_the_day_id(today), source=SOURCE_API, wotd_for_date=today
                    )
        except IntegrityError:
            # A concurrent first request of the day stored it first; serve that row.
            return await self.repo.get_word_of_the_day(today)
        except ServiceUnavailableError:
            logger.warning("Word of the Day not stored: vocabulary dataset not imported")
            return None
        return row
