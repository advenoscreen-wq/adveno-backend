"""Operational health endpoints."""

from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health", summary="Process health")
async def health() -> dict[str, str]:
    """Report that the API process is running."""
    return {"status": "ok"}


@router.get("/ready", summary="Dependency readiness")
async def ready(request: Request) -> dict[str, str]:
    """Report readiness based on configured critical dependencies."""
    database_ready = await request.app.state.check_database()
    if not database_ready:
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="Database is unavailable")
    return {"status": "ready"}
