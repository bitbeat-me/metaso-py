"""Data types for the Metaso client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class SearchResult:
    id: str
    title: str
    url: str
    snippet: str
    source: str  # "webpage", "scholar", "document", "paper", etc.


@dataclass
class SearchResponse:
    query: str
    results: list[SearchResult]
    summary: str | None = None
    session_id: str | None = None


@dataclass
class ReaderResponse:
    url: str
    content: str
    format: str  # "json" or "markdown"


@dataclass
class ChatResponse:
    message: str
    answer: str
    model: str = "fast"


@dataclass
class Topic:
    id: str
    name: str
    dir_root_id: str | None = None
    created_at: datetime | None = None


@dataclass
class File:
    id: str
    file_name: str
    parent_id: str
    progress: int = 0
    status: str = "processing"


@dataclass
class Book:
    id: str
    title: str
    file_id: str
    progress: int = 0
    status: str = "processing"


@dataclass
class UserInfo:
    uid: str
    nickname: str | None = None
    vip_level: int = 0
