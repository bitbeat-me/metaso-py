from __future__ import annotations

from metaso._core import ClientCore
from metaso.types import UserInfo


class UserAPI:
    def __init__(self, core: ClientCore):
        self._core = core

    async def info(self) -> UserInfo:
        return await self._core.backend.user_info()
