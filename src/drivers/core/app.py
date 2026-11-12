"""FastAPI application factory."""

from collections.abc import Callable

from fastapi import FastAPI

from config.logging import configure_logging
from config.settings import Settings, get_settings
from drivers.core.exception_handlers import register_exception_handlers
from drivers.database.database import (
    check_database,
    create_session_factory,
)
from drivers.database.transaction import DatabaseTransactionMiddleware
from drivers.routers.health import router as health_router
from drivers.routers.router import router as v1_router


def create_app(
    settings: Settings | None = None,
    database_check: Callable[[], object] | None = None,
) -> FastAPI:
    """Build the FastAPI application and wire infrastructure dependencies."""
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)
    app = FastAPI(title=resolved_settings.app_name, version=resolved_settings.app_version)
    register_exception_handlers(app)
    session_factory = create_session_factory(resolved_settings)
    app.add_middleware(DatabaseTransactionMiddleware, session_factory=session_factory)

    async def check_ready() -> bool:
        if database_check is not None:
            result = database_check()
            return bool(await result) if hasattr(result, "__await__") else bool(result)
        return await check_database(session_factory)

    app.state.settings = resolved_settings
    app.state.check_database = check_ready
    v1_router.include_router(health_router)
    app.include_router(v1_router)
    return app
