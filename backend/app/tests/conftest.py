from unittest.mock import patch

import app.modules.ai.models  # noqa: F401
import app.modules.communication.models  # noqa: F401
import app.modules.files.preview_models  # noqa: F401
import app.modules.goals.models  # noqa: F401

# Register Cycle 8 tables on Base before create_all (must run before importing FastAPI app,
# because `import app.modules...` would rebind the name `app` if done after `from app.main import app`).
import app.modules.habits.models  # noqa: F401
import app.modules.integrations.github.sync_models  # noqa: F401
import app.modules.integrations.models  # noqa: F401
import app.modules.integrations.reports.models  # noqa: F401
import app.modules.routines.models  # noqa: F401
import app.modules.tasks.models  # noqa: F401
import app.modules.wishlist.models  # noqa: F401
import httpx
import pytest
import pytest_asyncio
from app.core.database import Base, get_db
from app.main import app
from app.modules.ai.adapters import base as ai_adapter_base
from app.modules.auth.registration_gate import require_registration_unlock
from app.modules.integrations.wordnik import client as wordnik_client
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DB = "sqlite+aiosqlite:///:memory:"

# Sarvam's public model lists, returned whenever a test saves a Sarvam key.
SARVAM_MODEL_LISTS = {
    "/v1/models": {"object": "list", "data": [{"id": "sarvam-105b"}, {"id": "sarvam-105b-conversations"}]},
    "/v2/models": {"object": "list", "data": [{"id": "glm5.3"}, {"id": "sarvam-105b"}]},
}


def _offline_vendor(request: httpx.Request) -> httpx.Response:
    if request.url.host == "api.sarvam.ai" and request.url.path in SARVAM_MODEL_LISTS:
        return httpx.Response(200, json=SARVAM_MODEL_LISTS[request.url.path])
    return httpx.Response(503, json={"error": {"message": "LLM vendor network is disabled in tests"}})


@pytest.fixture(autouse=True)
def _no_real_llm_vendor_calls():
    """AI adapters and the Wordnik client never reach the internet in tests; individual tests mock vendors on top of this."""
    real_client = httpx.AsyncClient

    def offline_client(timeout: float) -> httpx.AsyncClient:
        return real_client(timeout=timeout, transport=httpx.MockTransport(_offline_vendor))

    with (
        patch.object(ai_adapter_base, "_http_client", side_effect=offline_client),
        patch.object(wordnik_client, "_http_client", side_effect=offline_client),
    ):
        yield


class FakeWordnik:
    """Routes Wordnik requests by path and records them. Tests edit `responses` / `status`."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.status: int | None = None  # force every response to this status
        self.usage: tuple[int, int] | None = (73, 100)  # (remaining, limit) headers
        self.responses: dict[str, object] = {
            "/v4/words.json/wordOfTheDay": {
                "word": "herald",
                "definitions": [{"text": "A <xref>messenger</xref> bearing news.", "partOfSpeech": "noun"}],
                "examples": [{"text": "The herald announced the king."}],
                "note": "From Old French.",
            },
            "/definitions": [
                {"text": "A <em>short</em> meaning.", "partOfSpeech": "noun"},
                {"partOfSpeech": "verb"},
            ],
            "/topExample": {"text": "An example sentence."},
            "/relatedWords": [
                {"relationshipType": "synonym", "words": ["envoy", "courier"]},
                {"relationshipType": "rhyme", "words": ["emerald"]},
            ],
            "/v4/words.json/reverseDictionary": {"results": [{"word": "acrophobia", "text": "fear of heights"}]},
            "/v4/words.json/randomWords": [{"word": w} for w in ("alpha", "bravo", "charlie", "delta")],
            "/v4/words.json/randomWord": {"word": "puzzle"},
        }

    def paths(self) -> list[str]:
        return [r.url.path for r in self.requests]

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        headers = {}
        if self.usage is not None:
            headers = {"X-RateLimit-Remaining-Hour": str(self.usage[0]), "X-RateLimit-Limit-Hour": str(self.usage[1])}
        if self.status is not None:
            return httpx.Response(self.status, json={"message": "forced"}, headers=headers)
        path = request.url.path
        for key, body in self.responses.items():
            if path == key or (key.startswith("/") and not key.startswith("/v4") and path.endswith(key)):
                if body is None:
                    return httpx.Response(404, json={"message": "not found"}, headers=headers)
                return httpx.Response(200, json=body, headers=headers)
        return httpx.Response(404, json={"message": "not found"}, headers=headers)


@pytest.fixture
def wordnik():
    """Mock Wordnik vendor for a test (overrides the autouse offline transport)."""
    fake = FakeWordnik()
    real_client = httpx.AsyncClient

    def factory(timeout: float) -> httpx.AsyncClient:
        return real_client(timeout=timeout, transport=httpx.MockTransport(fake))

    with patch.object(wordnik_client, "_http_client", side_effect=factory):
        yield fake


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(TEST_DB, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    # Existing suite registers users freely; gate tests clear this override explicitly.
    app.dependency_overrides[require_registration_unlock] = lambda: None
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Exposed so tests that need to seed rows directly (bypassing the HTTP API —
        # e.g. master vocabulary fixture data) can open a session against the same
        # in-memory test database. See test_communication_vocabulary_sequencing.py.
        ac.session_factory = session_factory
        yield ac
    app.dependency_overrides.clear()
    await engine.dispose()
