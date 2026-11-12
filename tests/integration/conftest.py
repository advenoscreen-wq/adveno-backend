"""Integration test configuration placeholder."""

import pytest


@pytest.fixture
def integration_database_url() -> str:
    """Return the configured integration database URL."""
    return "postgresql+asyncpg://adveno:adveno_dev_password@localhost:5432/adveno"
