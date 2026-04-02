"""Abstract backend base class with capability model."""
from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from pathlib import Path
from metaso.exceptions import BackendError
from metaso.types import Book, File, SearchResponse, SearchResult, Topic, UserInfo, ReaderResponse, ChatResponse


class BackendBase(ABC):
    @abstractmethod
    def capabilities(self) -> set[str]:
        """Return set of supported operation names."""

    def supports(self, operation: str) -> bool:
        return operation in self.capabilities()

    @abstractmethod
    async def search(self, query: str, scope: str = "webpage", stream: bool = False,
                     session_id: str | None = None, **kwargs) -> SearchResponse | AsyncIterator[dict]: ...

    async def read_url(self, url: str, format: str = "markdown") -> ReaderResponse:
        raise BackendError(f"{self.__class__.__name__} does not support read_url")

    async def chat(self, message: str, model: str = "fast") -> ChatResponse:
        raise BackendError(f"{self.__class__.__name__} does not support chat")

    async def create_topic(self, name: str) -> Topic:
        raise BackendError(f"{self.__class__.__name__} does not support create_topic")

    async def list_topics(self) -> list[Topic]:
        raise BackendError(f"{self.__class__.__name__} does not support list_topics")

    async def delete_topic(self, topic_id: str) -> bool:
        raise BackendError(f"{self.__class__.__name__} does not support delete_topic")

    async def upload_file(self, topic_id: str, file_path: Path) -> File:
        raise BackendError(f"{self.__class__.__name__} does not support upload_file")

    async def list_files(self, topic_id: str) -> list[File]:
        raise BackendError(f"{self.__class__.__name__} does not support list_files")

    async def delete_file(self, file_id: str) -> bool:
        raise BackendError(f"{self.__class__.__name__} does not support delete_file")

    async def add_book(self, topic_id: str, url: str) -> Book:
        raise BackendError(f"{self.__class__.__name__} does not support add_book")

    async def list_books(self, topic_id: str) -> list[Book]:
        raise BackendError(f"{self.__class__.__name__} does not support list_books")

    async def user_info(self) -> UserInfo:
        raise BackendError(f"{self.__class__.__name__} does not support user_info")
