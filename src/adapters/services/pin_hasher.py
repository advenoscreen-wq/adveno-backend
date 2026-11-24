"""Scrypt-based password hashing for short screen administration PINs."""

import asyncio
import base64
import hashlib
import hmac
import secrets


class ScryptPinHasher:
    _cost = 2**14
    _block_size = 8
    _parallelism = 1
    _key_length = 32

    async def hash_pin(self, pin: str) -> str:
        salt = secrets.token_bytes(16)
        key = await asyncio.to_thread(
            hashlib.scrypt,
            pin.encode("utf-8"),
            salt=salt,
            n=self._cost,
            r=self._block_size,
            p=self._parallelism,
            dklen=self._key_length,
        )
        return "$".join(
            (
                "scrypt",
                str(self._cost),
                str(self._block_size),
                str(self._parallelism),
                base64.urlsafe_b64encode(salt).decode("ascii"),
                base64.urlsafe_b64encode(key).decode("ascii"),
            )
        )

    async def verify_pin(self, encoded_hash: str, pin: str) -> bool:
        try:
            algorithm, cost, block_size, parallelism, salt_text, key_text = encoded_hash.split("$")
            if algorithm != "scrypt":
                return False
            salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
            expected_key = base64.urlsafe_b64decode(key_text.encode("ascii"))
            actual_key = await asyncio.to_thread(
                hashlib.scrypt,
                pin.encode("utf-8"),
                salt=salt,
                n=int(cost),
                r=int(block_size),
                p=int(parallelism),
                dklen=len(expected_key),
            )
        except (ValueError, TypeError, UnicodeError):
            return False
        return hmac.compare_digest(actual_key, expected_key)
