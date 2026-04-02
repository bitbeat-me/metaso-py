from __future__ import annotations

from metaso._core import ClientCore
from metaso.types import Book


class BookshelfAPI:
    def __init__(self, core: ClientCore):
        self._core = core

    async def add(self, topic_id: str, url: str) -> Book:
        return await self._core.backend.add_book(topic_id, url)

    async def list(self, topic_id: str) -> list[Book]:
        return await self._core.backend.list_books(topic_id)
