"""Shared test configuration."""

import pytest

from config.settings import Settings


@pytest.fixture
def test_settings() -> Settings:
    """Provide deterministic settings for tests."""
    return Settings(environment="test", database_url="postgresql+asyncpg://unused")
