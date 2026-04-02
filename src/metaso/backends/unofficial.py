"""Unofficial backend using reverse-engineered API with uid-sid cookie auth."""

from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator

import httpx

from metaso.auth import CookieAuth
from metaso.exceptions import AuthError, ServerError
from metaso.types import SearchResponse, SearchResult

from .base import BackendBase

BASE_URL = "https://metaso.cn"

FAKE_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Origin": "https://metaso.cn",
    "Sec-Ch-Ua": '"Chromium";v="130", "Google Chrome";v="130"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


class UnofficialBackend(BackendBase):
    def __init__(self, auth: CookieAuth, base_url: str = BASE_URL):
        self._auth = auth
        self._base_url = base_url.rstrip("/")
        self._http_client: httpx.AsyncClient | None = None
        self._meta_token: str | None = None

    def capabilities(self) -> set[str]:
        return {"search"}

    def _generate_cookie(self) -> str:
        return f"uid={self._auth.uid}; sid={self._auth.sid}"

    def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            raise RuntimeError("Backend not connected.")
        return self._http_client

    async def _acquire_meta_token(self) -> str:
        client = self._get_client()
        response = await client.get(
            f"{self._base_url}/",
            headers={**FAKE_HEADERS, "Cookie": self._generate_cookie()},
            follow_redirects=True,
        )
        if response.status_code != 200:
            raise AuthError(f"Failed to load Metaso homepage: {response.status_code}")
        match = re.search(r'<meta id="meta-token" content="([^"]*)"', response.text)
        if not match or not match.group(1):
            raise AuthError(
                "meta-token not found. Session may have expired. "
                "Run 'metaso login' to re-authenticate."
            )
        self._meta_token = match.group(1)
        return self._meta_token

    async def _ensure_meta_token(self) -> str:
        if self._meta_token is None:
            return await self._acquire_meta_token()
        return self._meta_token

    async def _create_session(self, question: str, mode: str) -> str:
        meta_token = await self._ensure_meta_token()
        engine_type = "scholar" if "scholar" in mode else "web"
        response = await self._get_client().post(
            f"{self._base_url}/api/session",
            json={
                "question": question,
                "mode": mode,
                "engineType": engine_type,
                "scholarSearchDomain": "all",
            },
            headers={
                **FAKE_HEADERS,
                "Cookie": self._generate_cookie(),
                "Token": meta_token,
                "Is-Mini-Webview": "0",
                "Content-Type": "application/json",
            },
        )
        if response.status_code != 200:
            raise ServerError(f"Failed to create session: {response.status_code}")
        return response.json()["data"]["id"]

    async def search(
        self,
        query: str,
        scope: str = "webpage",
        stream: bool = False,
        session_id: str | None = None,
        **kwargs,
    ) -> SearchResponse | AsyncIterator[dict]:
        # Map scope to mode for unofficial API
        mode = kwargs.get("mode", "detail")
        conv_id = session_id or await self._create_session(query, mode)
        if stream:
            return self._search_stream(query, conv_id)
        chunks = []
        async for chunk in self._search_stream(query, conv_id):
            chunks.append(chunk)
        return SearchResponse(
            query=query,
            results=self._extract_results(chunks),
            summary=self._extract_summary(chunks),
            session_id=conv_id,
        )

    async def _search_stream(self, query: str, conv_id: str) -> AsyncIterator[dict]:
        meta_token = await self._ensure_meta_token()
        client = self._get_client()
        from httpx_sse import aconnect_sse

        async with aconnect_sse(
            client,
            "GET",
            f"{self._base_url}/api/searchV2",
            params={"sessionId": conv_id},
            headers={**FAKE_HEADERS, "Cookie": self._generate_cookie(), "Token": meta_token},
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.data == "[DONE]":
                    break
                try:
                    yield json.loads(sse.data)
                except json.JSONDecodeError:
                    continue

    async def validate_auth(self) -> bool:
        """Check if current cookies are valid by fetching meta-token."""
        try:
            await self._acquire_meta_token()
            return True
        except AuthError:
            return False

    def _extract_results(self, chunks: list[dict]) -> list[SearchResult]:
        """Extract search results from SSE chunks."""
        results = []
        for chunk in chunks:
            if chunk.get("type") == "set-reference":
                for item in chunk.get("list", []):
                    results.append(
                        SearchResult(
                            id=str(item.get("index", "")),
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            snippet=item.get("article_type", ""),
                            source="webpage",
                        )
                    )
        return results

    def _extract_summary(self, chunks: list[dict]) -> str | None:
        texts = [chunk.get("text", "") for chunk in chunks if chunk.get("text")]
        return "".join(texts) if texts else None
