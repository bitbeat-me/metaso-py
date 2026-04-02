from __future__ import annotations

from metaso._core import ClientCore
from metaso.types import Book


class BookshelfAPI:
    def __init__(self, core: ClientCore):
        self._core = core

    async def add(self, url: str) -> Book:
        """Add a book/PDF by URL. Books are global (not per-topic in official API)."""
        return await self._core.backend.add_book("", url)
