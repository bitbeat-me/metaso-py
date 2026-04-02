import httpx
import pytest
import respx

from metaso.auth import ApiKeyAuth
from metaso.backends.official import OfficialBackend
from metaso.types import SearchResponse


@pytest.fixture
def auth():
    return ApiKeyAuth(api_key="sk-test")


@pytest.fixture
def backend(auth):
    return OfficialBackend(auth=auth)


SEARCH_RESPONSE_JSON = {
    "errCode": 0,
    "data": {
        "references": [
            {
                "index": 1,
                "title": "AI Trends 2026",
                "link": "https://example.com/ai",
                "article_type": "行业报告",
                "source": "webpage",
            }
        ],
        "sessionId": "sess-abc",
    },
}

READER_RESPONSE_JSON = {
    "errCode": 0,
    "data": {"content": "# Hello World", "url": "https://example.com"},
}
CHAT_RESPONSE_JSON = {"errCode": 0, "data": {"answer": "AI is artificial intelligence."}}


@respx.mock
@pytest.mark.asyncio
async def test_search_returns_search_response(backend):
    respx.post("https://metaso.cn/api/open/search/v2").mock(
        return_value=httpx.Response(200, json=SEARCH_RESPONSE_JSON)
    )
    async with httpx.AsyncClient() as http_client:
        backend._http_client = http_client
        result = await backend.search("AI trends")
    assert isinstance(result, SearchResponse)
    assert len(result.results) == 1
    assert result.results[0].title == "AI Trends 2026"
    assert result.session_id == "sess-abc"


@respx.mock
@pytest.mark.asyncio
async def test_search_sends_correct_headers(backend):
    route = respx.post("https://metaso.cn/api/open/search/v2").mock(
        return_value=httpx.Response(200, json=SEARCH_RESPONSE_JSON)
    )
    async with httpx.AsyncClient() as http_client:
        backend._http_client = http_client
        await backend.search("test")
    assert route.calls.last.request.headers["authorization"] == "Bearer sk-test"


@respx.mock
@pytest.mark.asyncio
async def test_read_url(backend):
    respx.post("https://metaso.cn/api/v1/reader").mock(
        return_value=httpx.Response(200, json=READER_RESPONSE_JSON)
    )
    async with httpx.AsyncClient() as http_client:
        backend._http_client = http_client
        result = await backend.read_url("https://example.com", format="markdown")
    assert result.content == "# Hello World"


@respx.mock
@pytest.mark.asyncio
async def test_chat(backend):
    respx.post("https://metaso.cn/api/v1/chat").mock(
        return_value=httpx.Response(200, json=CHAT_RESPONSE_JSON)
    )
    async with httpx.AsyncClient() as http_client:
        backend._http_client = http_client
        result = await backend.chat("what is AI")
    assert result.answer == "AI is artificial intelligence."


def test_capabilities(backend):
    caps = backend.capabilities()
    assert "search" in caps
    assert "read_url" in caps
    assert "chat" in caps


def test_supports(backend):
    assert backend.supports("search") is True
    assert backend.supports("create_topic") is True
