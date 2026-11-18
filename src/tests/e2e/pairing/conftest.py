"""Pairing API fixture alias for the shared end-to-end client."""

import httpx
import pytest


@pytest.fixture
def pairing_client(client: httpx.AsyncClient) -> httpx.AsyncClient:
    return client
