"""PIN password-hashing contract."""

from typing import Protocol


class PinHasher(Protocol):
    async def hash_pin(self, pin: str) -> str: ...

    async def verify_pin(self, encoded_hash: str, pin: str) -> bool: ...
