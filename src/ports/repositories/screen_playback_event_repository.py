"""Persistence contract for screen playback events."""

from collections.abc import Sequence
from typing import Protocol

from domain import ScreenPlaybackEvent


class ScreenPlaybackEventRepository(Protocol):
    async def save_many_idempotently(self, events: Sequence[ScreenPlaybackEvent]) -> int: ...
