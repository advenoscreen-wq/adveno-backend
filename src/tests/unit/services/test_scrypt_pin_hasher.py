"""Unit tests for the salted PIN password hasher."""

import pytest

from adapters.services.pin_hasher import ScryptPinHasher


@pytest.mark.asyncio
async def test_pin_hash_is_salted_and_verifies_only_matching_pin() -> None:
    hasher = ScryptPinHasher()

    first_hash = await hasher.hash_pin("001234")
    second_hash = await hasher.hash_pin("001234")

    assert first_hash.startswith("scrypt$")
    assert first_hash != "001234"
    assert first_hash != second_hash
    assert await hasher.verify_pin(first_hash, "001234")
    assert not await hasher.verify_pin(first_hash, "001235")
