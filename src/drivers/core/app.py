"""FastAPI application factory."""

from collections.abc import Callable
from inspect import isawaitable

from fastapi import FastAPI

from config.logging import configure_logging
from config.settings import Settings, get_settings
from drivers.core.exception_handlers import register_exception_handlers
from drivers.database.database import create_session_factory
from drivers.database.transaction import DatabaseTransactionMiddleware
from drivers.routers.dependencies import get_database_ready
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
    app.state.session_factory = session_factory
    app.dependency_overrides[get_settings] = lambda: resolved_settings
    if database_check is not None:

        async def check_ready() -> bool:
            result = database_check()
            return bool(await result) if isawaitable(result) else bool(result)

        app.dependency_overrides[get_database_ready] = check_ready
    app.include_router(v1_router)
    return app
