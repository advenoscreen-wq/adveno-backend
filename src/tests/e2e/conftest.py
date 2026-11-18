"""Reuse the real PostgreSQL/Redis-backed API fixtures for end-to-end tests."""

pytest_plugins = (
    "tests.integration.conftest",
    "tests.integration.api.conftest",
)
