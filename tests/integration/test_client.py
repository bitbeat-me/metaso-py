import httpx
import pytest
import respx
from metaso.client import MetasoClient

SEARCH_RESPONSE = {"errCode": 0, "data": {"items": [{"id": "1", "title": "T", "url": "https://x.com", "snippet": "s", "source": "webpage"}], "sessionId": "s1"}}
READER_RESPONSE = {"errCode": 0, "data": {"content": "# Hello", "url": "https://example.com"}}
CHAT_RESPONSE = {"errCode": 0, "data": {"answer": "42"}}


@respx.mock
@pytest.mark.asyncio
async def test_client_from_api_key():
    respx.post("https://metaso.cn/api/open/search/v2").mock(return_value=httpx.Response(200, json=SEARCH_RESPONSE))
    async with MetasoClient.from_api_key("sk-test") as client:
        result = await client.search.query("test")
        assert result.query == "test"


@respx.mock
@pytest.mark.asyncio
async def test_client_reader():
    respx.post("https://metaso.cn/api/v1/reader").mock(return_value=httpx.Response(200, json=READER_RESPONSE))
    async with MetasoClient.from_api_key("sk-test") as client:
        result = await client.reader.read("https://example.com")
        assert result.content == "# Hello"


@respx.mock
@pytest.mark.asyncio
async def test_client_chat():
    respx.post("https://metaso.cn/api/v1/chat").mock(return_value=httpx.Response(200, json=CHAT_RESPONSE))
    async with MetasoClient.from_api_key("sk-test") as client:
        result = await client.chat.ask("meaning of life")
        assert result.answer == "42"


@respx.mock
@pytest.mark.asyncio
async def test_client_auto_with_env(monkeypatch):
    monkeypatch.setenv("METASO_API_KEY", "sk-env")
    respx.post("https://metaso.cn/api/open/search/v2").mock(return_value=httpx.Response(200, json=SEARCH_RESPONSE))
    async with MetasoClient.auto() as client:
        result = await client.search.query("test")
        assert result.query == "test"


@pytest.mark.asyncio
async def test_client_auto_no_credentials(monkeypatch, tmp_path):
    monkeypatch.delenv("METASO_API_KEY", raising=False)
    monkeypatch.setenv("METASO_HOME", str(tmp_path))
    with pytest.raises(ValueError, match="No credentials found"):
        MetasoClient.auto()
