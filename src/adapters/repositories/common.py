"""Shared repository persistence helpers."""

import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from inspect import iscoroutinefunction

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from domain.exceptions import PersistenceConflictError


def _logged_operation[**P, R](
    operation: Callable[P, Awaitable[R]], *, logger: logging.Logger, repository: str
) -> Callable[P, Awaitable[R]]:
    @wraps(operation)
    async def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        extra = {"repository": repository, "operation": operation.__name__}
        logger.debug("Repository operation started", extra=extra)
        try:
            result = await operation(*args, **kwargs)
        except Exception as error:
            logger.error(
                "Repository operation failed",
                extra={**extra, "error_type": type(error).__name__},
            )
            raise
        logger.debug("Repository operation completed", extra=extra)
        return result

    return wrapped


def log_repository_operations[RepositoryType: type](
    repository_class: RepositoryType,
) -> RepositoryType:
    """Log calls and failures for every public async repository method."""
    logger = logging.getLogger(repository_class.__module__)
    for name, operation in vars(repository_class).items():
        if not name.startswith("_") and iscoroutinefunction(operation):
            setattr(
                repository_class,
                name,
                _logged_operation(operation, logger=logger, repository=repository_class.__name__),
            )
    return repository_class


async def flush_session(session: AsyncSession, operation: str) -> None:
    """Flush a repository transaction and translate integrity conflicts."""
    try:
        await session.flush()
    except IntegrityError as error:
        logging.getLogger(__name__).warning(
            "Repository flush rejected by a persistence constraint",
            extra={"operation": operation},
        )
        await session.rollback()
        raise PersistenceConflictError(f"{operation} violates a persistence constraint") from error
