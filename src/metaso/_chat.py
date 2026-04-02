from __future__ import annotations

from metaso._core import ClientCore
from metaso.types import ChatResponse


class ChatAPI:
    def __init__(self, core: ClientCore):
        self._core = core

    async def ask(self, message: str, model: str = "fast") -> ChatResponse:
        return await self._core.backend.chat(message, model=model)
