"""Travel OS routers, mounted under /api/v1/travel. Every endpoint requires a signed-in user."""

from fastapi import APIRouter

from app.modules.travel.api import adventures, maps, memories, places, routes, trips, usage, world

router = APIRouter(prefix="/travel", tags=["travel"])
router.include_router(places.router)
router.include_router(maps.router)
router.include_router(trips.router)
router.include_router(routes.router)
router.include_router(adventures.router)
router.include_router(memories.router)
router.include_router(world.router)
router.include_router(usage.router)
