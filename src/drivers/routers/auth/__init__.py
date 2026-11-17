"""Authentication routes."""

from fastapi import APIRouter

from drivers.routers.auth.google import router as google_router
from drivers.routers.auth.session import router as session_router

router = APIRouter(prefix="/auth")
router.include_router(google_router)
router.include_router(session_router)
