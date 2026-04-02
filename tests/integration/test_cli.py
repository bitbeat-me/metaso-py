import httpx
import respx
from click.testing import CliRunner

from metaso.cli import cli

SEARCH_RESPONSE = {
    "errCode": 0,
    "data": {
        "items": [
            {
                "id": "1",
                "title": "AI Result",
                "url": "https://x.com",
                "snippet": "test snippet",
                "source": "webpage",
            }
        ],
        "sessionId": "s1",
    },
}
READER_RESPONSE = {"errCode": 0, "data": {"content": "# Hello World", "url": "https://example.com"}}
CHAT_RESPONSE = {"errCode": 0, "data": {"answer": "The answer is 42."}}


@respx.mock
def test_search_command(monkeypatch):
    monkeypatch.setenv("METASO_API_KEY", "sk-test")
    respx.post("https://metaso.cn/api/open/search/v2").mock(
        return_value=httpx.Response(200, json=SEARCH_RESPONSE)
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["search", "AI trends"])
    assert result.exit_code == 0
    assert "AI Result" in result.output


@respx.mock
def test_search_json_output(monkeypatch):
    monkeypatch.setenv("METASO_API_KEY", "sk-test")
    respx.post("https://metaso.cn/api/open/search/v2").mock(
        return_value=httpx.Response(200, json=SEARCH_RESPONSE)
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["search", "test", "--json"])
    assert result.exit_code == 0
    import json

    data = json.loads(result.output)
    assert data["query"] == "test"


@respx.mock
def test_read_command(monkeypatch):
    monkeypatch.setenv("METASO_API_KEY", "sk-test")
    respx.post("https://metaso.cn/api/v1/reader").mock(
        return_value=httpx.Response(200, json=READER_RESPONSE)
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["read", "https://example.com"])
    assert result.exit_code == 0
    assert "Hello World" in result.output


@respx.mock
def test_chat_command(monkeypatch):
    monkeypatch.setenv("METASO_API_KEY", "sk-test")
    respx.post("https://metaso.cn/api/v1/chat").mock(
        return_value=httpx.Response(200, json=CHAT_RESPONSE)
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["chat", "meaning of life"])
    assert result.exit_code == 0
    assert "42" in result.output


def test_status_no_credentials(monkeypatch, tmp_path):
    monkeypatch.delenv("METASO_API_KEY", raising=False)
    monkeypatch.setenv("METASO_HOME", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "not configured" in result.output


def test_config_set_api_key(monkeypatch, tmp_path):
    monkeypatch.setenv("METASO_HOME", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "set", "api-key", "sk-new"])
    assert result.exit_code == 0
    assert "saved" in result.output
