"""Versioned API router composition."""

from fastapi import APIRouter

from drivers.routers.auth import router as auth_router
from drivers.routers.health import router as health_router
from drivers.routers.media import router as media_router
from drivers.routers.pairing import router as pairing_router
from drivers.routers.screens import router as screens_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(pairing_router)
router.include_router(media_router)
router.include_router(screens_router)
