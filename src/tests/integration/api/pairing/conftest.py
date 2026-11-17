"""Pairing API client alias for shared database-backed test setup."""

import httpx
import pytest


@pytest.fixture
def pairing_client(client: httpx.AsyncClient) -> httpx.AsyncClient:
    return client
