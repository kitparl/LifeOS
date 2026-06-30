from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.core.config import get_settings
from app.core.database import Base, engine
from app.modules.ai.api import router as ai_router
from app.modules.analytics.api import router as analytics_router
from app.modules.auth.api import router as auth_router
from app.modules.calendar.api import router as calendar_router
from app.modules.career.api import router as career_router
from app.modules.communication.api import router as communication_router
from app.modules.dashboard.api import router as dashboard_router
from app.modules.export.api import router as export_router
from app.modules.files.api import router as files_router
from app.modules.finance.api import router as finance_router
from app.modules.goals.api import router as goals_router
from app.modules.habits.api import router as habits_router
from app.modules.journal.api import router as journal_router
from app.modules.learning.api import router as learning_router
from app.modules.mood.api import router as mood_router
from app.modules.notifications.api import router as notifications_router
from app.modules.qa.api import router as qa_router
from app.modules.reports.api import router as reports_router
from app.modules.running.api import router as running_router
from app.modules.search.api import router as search_router
from app.modules.tasks.api import router as tasks_router
from app.modules.life_timeline.api import router as life_timeline_router
from app.modules.memory.api import router as memory_router
from app.modules.coaches.api import router as coaches_router
from app.modules.ocr.api import router as ocr_router
from app.modules.voice.api import router as voice_router
from app.modules.integrations.api import router as integrations_router
from app.modules.automations.api import router as automations_router
from app.modules.predictions.api import router as predictions_router
from app.modules.timeline.api import router as timeline_router
from app.modules.wishlist.api import router as wishlist_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)
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
app.include_router(ai_router, prefix="/api/v1")
app.include_router(learning_router, prefix="/api/v1")
app.include_router(career_router, prefix="/api/v1")
app.include_router(finance_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(timeline_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(memory_router, prefix="/api/v1")
app.include_router(coaches_router, prefix="/api/v1")
app.include_router(ocr_router, prefix="/api/v1")
app.include_router(voice_router, prefix="/api/v1")
app.include_router(integrations_router, prefix="/api/v1")
app.include_router(automations_router, prefix="/api/v1")
app.include_router(predictions_router, prefix="/api/v1")
app.include_router(life_timeline_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "env": settings.app_env,
        "production": settings.is_production,
    }


STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def _register_spa_routes() -> None:
    if not STATIC_DIR.is_dir():
        return

    @app.get("/")
    async def spa_index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/{full_path:path}")
    async def spa_files(full_path: str):
        if full_path.startswith("api/") or full_path == "health":
            raise HTTPException(status_code=404, detail="Not found")
        candidate = STATIC_DIR / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        index = STATIC_DIR / "index.html"
        if index.is_file():
            return FileResponse(index)
        raise HTTPException(status_code=404, detail="Not found")


_register_spa_routes()
