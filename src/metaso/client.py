from __future__ import annotations

import logging
import os

from metaso._bookshelf import BookshelfAPI
from metaso._chat import ChatAPI
from metaso._core import DEFAULT_TIMEOUT, ClientCore
from metaso._files import FilesAPI
from metaso._reader import ReaderAPI
from metaso._search import SearchAPI
from metaso._topics import TopicsAPI
from metaso._user import UserAPI
from metaso.auth import ApiKeyAuth, CookieAuth
from metaso.backends.official import OfficialBackend
from metaso.paths import get_cookie_path

logger = logging.getLogger(__name__)


class MetasoClient:
    def __init__(self, backend, timeout: float = DEFAULT_TIMEOUT):
        self._core = ClientCore(backend, timeout=timeout)
        self.search = SearchAPI(self._core)
        self.reader = ReaderAPI(self._core)
        self.chat = ChatAPI(self._core)
        self.topics = TopicsAPI(self._core)
        self.files = FilesAPI(self._core)
        self.bookshelf = BookshelfAPI(self._core)
        self.user = UserAPI(self._core)

    async def __aenter__(self) -> MetasoClient:
        await self._core.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._core.close()

    @property
    def is_connected(self) -> bool:
        return self._core.is_open

    @classmethod
    def from_api_key(cls, api_key: str, **kwargs) -> MetasoClient:
        auth = ApiKeyAuth(api_key=api_key)
        backend = OfficialBackend(auth=auth)
        return cls(backend, **kwargs)

    @classmethod
    def from_storage(cls, profile: str | None = None, **kwargs) -> MetasoClient:
        cookie_path = get_cookie_path(profile)
        auth = CookieAuth.from_storage(cookie_path)
        from metaso.backends.unofficial import UnofficialBackend
        backend = UnofficialBackend(auth=auth)
        return cls(backend, **kwargs)

    @classmethod
    def auto(cls, **kwargs) -> MetasoClient:
        api_key = os.environ.get("METASO_API_KEY")
        if api_key:
            return cls.from_api_key(api_key, **kwargs)
        try:
            return cls.from_storage(**kwargs)
        except FileNotFoundError:
            raise ValueError(
                "No credentials found. Either:\n"
                "  1. Set METASO_API_KEY environment variable, or\n"
                "  2. Run 'metaso login' to authenticate via browser."
            )
