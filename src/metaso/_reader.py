from __future__ import annotations

from metaso._core import ClientCore
from metaso.types import ReaderResponse


class ReaderAPI:
    def __init__(self, core: ClientCore):
        self._core = core

    async def read(self, url: str, format: str = "markdown") -> ReaderResponse:
        return await self._core.backend.read_url(url, format=format)
