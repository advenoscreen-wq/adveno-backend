"""Operational health endpoints."""

from fastapi import APIRouter, HTTPException

from drivers.routers.dependencies import DatabaseReady

router = APIRouter(tags=["health"])


@router.get("/health", summary="Process health")
async def health() -> dict[str, str]:
    """Report that the API process is running."""
    return {"status": "ok"}


@router.get("/ready", summary="Dependency readiness")
async def ready(database_ready: DatabaseReady) -> dict[str, str]:
    """Report readiness based on configured critical dependencies."""
    if not database_ready:
        raise HTTPException(status_code=503, detail="Database is unavailable")
    return {"status": "ready"}
