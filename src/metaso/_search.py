from __future__ import annotations
from collections.abc import AsyncIterator
from metaso._core import ClientCore
from metaso.types import SearchResponse


class SearchAPI:
    def __init__(self, core: ClientCore):
        self._core = core

    async def query(self, question: str, scope: str = "webpage", stream: bool = False,
                    session_id: str | None = None, **kwargs) -> SearchResponse | AsyncIterator[dict]:
        return await self._core.backend.search(query=question, scope=scope, stream=stream,
                                                session_id=session_id, **kwargs)
