from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.database import Base, engine
from app.modules.auth.api import router as auth_router
from app.modules.dashboard.api import router as dashboard_router
from app.modules.goals.api import router as goals_router
from app.modules.habits.api import router as habits_router
from app.modules.tasks.api import router as tasks_router

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

@app.get("/health")
async def health():
    return {"status": "ok"}
