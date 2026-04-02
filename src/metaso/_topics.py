from __future__ import annotations

from metaso._core import ClientCore
from metaso.types import Topic


class TopicsAPI:
    def __init__(self, core: ClientCore):
        self._core = core

    async def create(self, name: str) -> Topic:
        return await self._core.backend.create_topic(name)

    async def list(self) -> list[Topic]:
        return await self._core.backend.list_topics()

    async def delete(self, topic_id: str) -> bool:
        return await self._core.backend.delete_topic(topic_id)
