"""Metaso AI Search Python Client."""

__version__ = "0.1.0"

from metaso.client import MetasoClient
from metaso.exceptions import (
    AuthError,
    BackendError,
    MetasoError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from metaso.types import (
    Book,
    ChatResponse,
    File,
    ReaderResponse,
    SearchResponse,
    SearchResult,
    Topic,
    UserInfo,
)

__all__ = [
    "MetasoClient",
    "SearchResult",
    "SearchResponse",
    "ReaderResponse",
    "ChatResponse",
    "Topic",
    "File",
    "Book",
    "UserInfo",
    "MetasoError",
    "AuthError",
    "BackendError",
    "NetworkError",
    "RateLimitError",
    "ServerError",
    "NotFoundError",
    "ValidationError",
]
