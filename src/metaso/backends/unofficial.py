"""Unofficial backend using browser-based search with uid-sid cookie auth."""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import AsyncIterator

import httpx

from metaso.auth import CookieAuth
from metaso.exceptions import AuthError, BackendError, ServerError
from metaso.types import SearchResponse, SearchResult

from .base import BackendBase

BASE_URL = "https://metaso.cn"

FAKE_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Origin": "https://metaso.cn",
}


def _run_browser(*args: str, timeout: int = 60) -> str | None:
    """Run agent-browser with --session-name metaso."""
    try:
        result = subprocess.run(
            ["agent-browser", "--session-name", "metaso", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = (result.stdout or "") + (result.stderr or "")
        return output.strip() if output.strip() else ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


class UnofficialBackend(BackendBase):
    """Backend using browser-based search with cookie auth.

    Search is performed by navigating the browser to metaso.cn/search/{convId}?q={query},
    which triggers the page's internal search API. Results are extracted from the page.

    Requires agent-browser to be installed and a valid session from `metaso login`.
    """

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
        """Fetch meta-token from the Metaso homepage."""
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

    async def validate_auth(self) -> bool:
        try:
            await self._acquire_meta_token()
            return True
        except AuthError:
            return False

    async def _create_session(self, question: str, mode: str) -> str:
        """Create a search session and return conversation ID."""
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
        data = response.json()
        if data.get("errCode") != 0:
            raise ServerError(f"Session error: {data.get('errMsg', 'unknown')}")
        return str(data["data"]["id"])

    async def search(
        self,
        query: str,
        scope: str = "webpage",
        stream: bool = False,
        session_id: str | None = None,
        **kwargs,
    ) -> SearchResponse | AsyncIterator[dict]:
        """Execute search by navigating browser to metaso.cn/search/{convId}?q={query}.

        This triggers the page's internal search API. Results are extracted from
        the page after search completes.
        """
        import urllib.parse

        mode = kwargs.get("mode", "detail")
        conv_id = session_id or await self._create_session(query, mode)

        # Navigate browser to trigger search
        encoded_q = urllib.parse.quote(query)
        search_url = f"{self._base_url}/search/{conv_id}?q={encoded_q}"

        result = _run_browser("open", search_url, timeout=30)
        if result is None:
            raise BackendError(
                "agent-browser not available. Unofficial backend requires agent-browser. "
                "Use official backend (API key) instead."
            )

        # Wait for search to complete (networkidle means SSE stream finished)
        _run_browser("wait", "--load", "networkidle", timeout=120)

        # Extract results from the page
        _selector = (
            ".search-result, .result-content, [class*=result], [class*=answer], main"
        )
        _ref_filter = "[class*=ref], [class*=source], [class*=citation]"
        _js = (
            "JSON.stringify({"
            "title: document.title,"
            f"text: document.querySelector('{_selector}')?.innerText"
            " || document.body.innerText.substring(0, 5000),"
            f"refs: Array.from(document.querySelectorAll('a[href]'))"
            f".filter(a => a.closest('{_ref_filter}'))"
            ".map(a => ({title: a.textContent?.trim(), url: a.href}))"
            ".filter(r => r.url.startsWith('http') && !r.url.includes('metaso.cn'))"
            ".slice(0, 30)})"
        )
        page_data = _run_browser("eval", _js, timeout=15)

        results = []
        summary = ""
        try:
            if page_data:
                data = json.loads(page_data)
                summary = data.get("text", "")
                for i, ref in enumerate(data.get("refs", []), 1):
                    results.append(
                        SearchResult(
                            id=str(i),
                            title=ref.get("title", ""),
                            url=ref.get("url", ""),
                            snippet="",
                            source="webpage",
                        )
                    )
        except (json.JSONDecodeError, KeyError):
            pass

        return SearchResponse(
            query=query,
            results=results,
            summary=summary if summary else None,
            session_id=conv_id,
        )
