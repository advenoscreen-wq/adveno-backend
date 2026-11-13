"""Authentication routes."""

from fastapi import APIRouter

from drivers.routers.auth.google import router as google_router

router = APIRouter(prefix="/auth")
router.include_router(google_router)
