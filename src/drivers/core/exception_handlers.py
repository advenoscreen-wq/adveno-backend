"""HTTP exception handling."""

import logging

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unexpected failures and return a safe error envelope."""
    logger.exception("Unhandled request error", extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "status_code": 500,
            }
        },
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return HTTP errors in the documented error envelope."""
    if isinstance(exc, HTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
        status_code = exc.status_code
    else:
        detail = "Request failed."
        status_code = 500
    code = "SERVICE_UNAVAILABLE" if status_code == 503 else "HTTP_ERROR"
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": detail,
                "status_code": status_code,
            }
        },
    )


def register_exception_handlers(app: object) -> None:
    """Register global exception handlers on a FastAPI application."""
    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        raise TypeError("app must be a FastAPI instance")
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unexpected_exception_handler)
