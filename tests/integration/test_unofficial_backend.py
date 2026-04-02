import httpx
import pytest
import respx

from metaso.auth import CookieAuth
from metaso.backends.unofficial import UnofficialBackend

META_TOKEN_HTML = '<html><meta id="meta-token" content="test-meta-token-123"></html>'


@pytest.fixture
def auth():
    return CookieAuth(uid="test-uid", sid="test-sid")


@pytest.fixture
def backend(auth):
    return UnofficialBackend(auth=auth)


def test_capabilities(backend):
    caps = backend.capabilities()
    assert "search" in caps


@respx.mock
@pytest.mark.asyncio
async def test_acquire_meta_token(backend):
    respx.get("https://metaso.cn/").mock(return_value=httpx.Response(200, text=META_TOKEN_HTML))
    async with httpx.AsyncClient() as http_client:
        backend._http_client = http_client
        token = await backend._acquire_meta_token()
    assert token == "test-meta-token-123"


def test_generate_cookie(backend):
    cookie = backend._generate_cookie()
    assert cookie == "uid=test-uid; sid=test-sid"


@respx.mock
@pytest.mark.asyncio
async def test_meta_token_not_found_raises_auth_error(backend):
    respx.get("https://metaso.cn/").mock(
        return_value=httpx.Response(200, text="<html>no token here</html>")
    )
    async with httpx.AsyncClient() as http_client:
        backend._http_client = http_client
        from metaso.exceptions import AuthError

        with pytest.raises(AuthError, match="meta-token not found"):
            await backend._acquire_meta_token()
