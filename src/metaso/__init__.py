"""Metaso AI Search Python Client."""
__version__ = "0.1.0"

from metaso.client import MetasoClient
from metaso.types import Book, File, SearchResponse, SearchResult, ReaderResponse, ChatResponse, Topic, UserInfo
from metaso.exceptions import (
    AuthError, BackendError, MetasoError, NetworkError,
    NotFoundError, RateLimitError, ServerError, ValidationError,
)

__all__ = [
    "MetasoClient", "SearchResult", "SearchResponse", "ReaderResponse", "ChatResponse",
    "Topic", "File", "Book", "UserInfo",
    "MetasoError", "AuthError", "BackendError", "NetworkError",
    "RateLimitError", "ServerError", "NotFoundError", "ValidationError",
]
