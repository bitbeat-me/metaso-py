"""Core infrastructure for the Metaso client."""
from __future__ import annotations
import logging
import httpx
from metaso.backends.base import BackendBase

logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 30.0
DEFAULT_CONNECT_TIMEOUT = 10.0
USER_AGENT = "metaso-py/0.1.0"


class ClientCore:
    def __init__(self, backend: BackendBase, timeout: float = DEFAULT_TIMEOUT):
        self._backend = backend
        self._timeout = timeout
        self._http_client: httpx.AsyncClient | None = None

    @property
    def backend(self) -> BackendBase:
        return self._backend

    @property
    def is_open(self) -> bool:
        return self._http_client is not None and not self._http_client.is_closed

    async def open(self) -> None:
        if self._http_client is not None:
            return
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout, connect=DEFAULT_CONNECT_TIMEOUT),
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )
        self._backend._http_client = self._http_client

    async def close(self) -> None:
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None
            self._backend._http_client = None
