from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.database import Base, engine
from app.modules.auth.api import router as auth_router
from app.modules.calendar.api import router as calendar_router
from app.modules.communication.api import router as communication_router
from app.modules.dashboard.api import router as dashboard_router
from app.modules.export.api import router as export_router
from app.modules.files.api import router as files_router
from app.modules.goals.api import router as goals_router
from app.modules.habits.api import router as habits_router
from app.modules.journal.api import router as journal_router
from app.modules.mood.api import router as mood_router
from app.modules.notifications.api import router as notifications_router
from app.modules.qa.api import router as qa_router
from app.modules.running.api import router as running_router
from app.modules.search.api import router as search_router
from app.modules.tasks.api import router as tasks_router
from app.modules.wishlist.api import router as wishlist_router

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(goals_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(habits_router, prefix="/api/v1")
app.include_router(running_router, prefix="/api/v1")
app.include_router(calendar_router, prefix="/api/v1")
app.include_router(journal_router, prefix="/api/v1")
app.include_router(mood_router, prefix="/api/v1")
app.include_router(communication_router, prefix="/api/v1")
app.include_router(qa_router, prefix="/api/v1")
app.include_router(wishlist_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
app.include_router(files_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok"}
