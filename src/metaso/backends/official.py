"""Official Metaso backend using API key authentication."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import httpx

from metaso.auth import ApiKeyAuth
from metaso.backends.base import BackendBase
from metaso.exceptions import AuthError, BackendError, RateLimitError, ServerError
from metaso.types import (
    Book,
    ChatResponse,
    File,
    ReaderResponse,
    SearchResponse,
    SearchResult,
    Topic,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://metaso.cn"


class OfficialBackend(BackendBase):
    """Backend that uses the official Metaso API with API key auth."""

    def __init__(self, auth: ApiKeyAuth) -> None:
        self._auth = auth
        self._http_client: httpx.AsyncClient | None = None

    def capabilities(self) -> set[str]:
        return {
            "search",
            "read_url",
            "chat",
            "create_topic",
            "delete_topic",
            "upload_file",
            "delete_file",
            "add_book",
        }

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": self._auth.header_value}

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an authenticated request and return parsed JSON response."""
        if self._http_client is None:
            raise BackendError("HTTP client not initialized. Use client as async context manager.")

        url = f"{BASE_URL}{path}"
        headers = {**self._auth_headers(), **(kwargs.pop("headers", {}))}

        response = await self._http_client.request(method, url, headers=headers, **kwargs)

        if response.status_code == 401:
            raise AuthError("Authentication failed. Check your API key.")
        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded.")
        if response.status_code >= 500:
            raise ServerError(f"Server error: {response.status_code}")

        response.raise_for_status()
        data = response.json()

        err_code = data.get("errCode", 0)
        if err_code == 401:
            raise AuthError("Authentication failed. Check your API key.")
        if err_code == 429:
            raise RateLimitError("Rate limit exceeded.")
        if err_code != 0:
            raise BackendError(f"API error {err_code}: {data.get('errMsg', 'Unknown error')}")

        return data

    async def search(
        self,
        query: str,
        scope: str = "webpage",
        stream: bool = False,
        session_id: str | None = None,
        **kwargs: Any,
    ) -> SearchResponse | AsyncIterator[dict]:
        """Search using the official API."""
        if stream:
            return self._search_stream(query, scope=scope, session_id=session_id, **kwargs)

        mode = kwargs.get("mode")
        body: dict[str, Any] = {"question": query, "lang": "zh", "stream": False}
        if scope and scope != "webpage":
            body["scope"] = scope
        if mode:
            body["mode"] = mode
        if session_id:
            body["sessionId"] = session_id

        data = await self._request("POST", "/api/open/search/v2", json=body)
        payload = data.get("data", {})
        # Official API returns "references" (not "items")
        items = payload.get("references", payload.get("items", []))
        results = [
            SearchResult(
                id=str(item.get("index", item.get("id", ""))),
                title=item.get("title", ""),
                url=item.get("link", item.get("url", "")),
                snippet=item.get("snippet", item.get("article_type", "")),
                source=item.get("source", "webpage"),
            )
            for item in items
        ]
        return SearchResponse(
            query=query,
            results=results,
            summary=payload.get("text"),
            session_id=str(payload.get("sessionId", "")) if payload.get("sessionId") else None,
        )

    async def _search_stream(
        self,
        query: str,
        scope: str = "webpage",
        session_id: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict]:
        """Stream search results via SSE."""
        from httpx_sse import aconnect_sse

        if self._http_client is None:
            raise BackendError("HTTP client not initialized.")

        mode = kwargs.get("mode")
        body: dict[str, Any] = {"question": query, "lang": "zh", "stream": True}
        if scope and scope != "webpage":
            body["scope"] = scope
        if mode:
            body["mode"] = mode
        if session_id:
            body["sessionId"] = session_id

        url = f"{BASE_URL}/api/open/search/v2"
        headers = self._auth_headers()

        async with aconnect_sse(
            self._http_client, "POST", url, headers=headers, json=body
        ) as event_source:
            async for event in event_source.aiter_sse():
                if event.data == "[DONE]":
                    break
                try:
                    yield json.loads(event.data)
                except json.JSONDecodeError:
                    continue

    async def read_url(self, url: str, format: str = "markdown") -> ReaderResponse:
        """Read a URL using the reader API."""
        data = await self._request("POST", "/api/v1/reader", json={"url": url, "format": format})
        # API returns {"markdown": "...", "title": "...", "url": "..."} at top level
        content = data.get("markdown", data.get("content", ""))
        return ReaderResponse(
            url=data.get("url", url),
            content=content,
            format=format,
        )

    async def chat(self, message: str, model: str = "fast") -> ChatResponse:
        """Chat via search API with concise mode (no standalone chat endpoint)."""
        data = await self._request(
            "POST",
            "/api/open/search/v2",
            json={"question": message, "lang": "zh", "stream": False, "mode": model},
        )
        payload = data.get("data", {})
        return ChatResponse(
            message=message,
            answer=payload.get("text", ""),
            model=model,
        )

    async def create_topic(self, name: str) -> Topic:
        data = await self._request("PUT", "/api/open/topic", json={"name": name})
        payload = data.get("data", {})
        return Topic(
            id=payload.get("id", ""),
            name=payload.get("name", name),
            dir_root_id=payload.get("dirRootId"),
        )

    async def delete_topic(self, topic_id: str) -> bool:
        await self._request("POST", "/api/open/topic/trash", json={"ids": [topic_id]})
        return True

    async def upload_file(self, topic_id: str, file_path: Path) -> File:
        """Upload file. topic_id here must be the dirRootId, not the topic id."""
        with open(file_path, "rb") as f:
            data = await self._request(
                "PUT",
                f"/api/open/file/{topic_id}",
                files={"file": (file_path.name, f)},
            )
        file_data = data.get("data", [{}])[0]
        return File(
            id=file_data.get("id", ""),
            file_name=file_data.get("fileName", file_path.name),
            parent_id=file_data.get("parentId", topic_id),
            progress=file_data.get("progress", 0),
        )

    async def check_file_progress(self, file_id: str) -> int:
        """Check file processing progress (0-100)."""
        data = await self._request("GET", f"/api/open/file/{file_id}/progress")
        return data.get("data", 0)

    async def delete_file(self, file_id: str) -> bool:
        await self._request("POST", "/api/open/file/trash", json={"ids": [file_id]})
        return True

    async def add_book(self, topic_id: str, url: str) -> Book:
        """Add book. Note: books are global, topic_id is ignored by official API."""
        data = await self._request("PUT", "/api/open/book", json={"url": url})
        payload = data.get("data", {})
        return Book(
            id=payload.get("id", ""),
            title=payload.get("title", ""),
            file_id=payload.get("fileId", ""),
            progress=payload.get("progress", 0),
        )
