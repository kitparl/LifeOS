import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Register Cycle 8 tables on Base before create_all (must run before importing FastAPI app,
# because `import app.modules...` would rebind the name `app` if done after `from app.main import app`).
import app.modules.habits.models  # noqa: F401
import app.modules.goals.models  # noqa: F401
import app.modules.integrations.report_models  # noqa: F401
import app.modules.integrations.github_sync_models  # noqa: F401
import app.modules.routines.models  # noqa: F401
import app.modules.wishlist.models  # noqa: F401
import app.modules.tasks.models  # noqa: F401

from app.core.database import Base, get_db
from app.main import app

TEST_DB = "sqlite+aiosqlite:///:memory:"

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
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    await engine.dispose()
