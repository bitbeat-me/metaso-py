import json
from pathlib import Path
from metaso.auth import ApiKeyAuth, CookieAuth

def test_api_key_auth():
    auth = ApiKeyAuth(api_key="sk-test123")
    assert auth.api_key == "sk-test123"
    assert auth.header_value == "Bearer sk-test123"

def test_cookie_auth():
    auth = CookieAuth(uid="abc123", sid="def456")
    assert auth.token == "abc123-def456"
    assert auth.header_value == "Bearer abc123-def456"

def test_cookie_auth_from_dict():
    cookies = {"uid": "abc123", "sid": "def456"}
    auth = CookieAuth.from_cookies(cookies)
    assert auth.uid == "abc123"
    assert auth.sid == "def456"

def test_cookie_auth_from_dict_missing_key():
    import pytest
    with pytest.raises(ValueError, match="Missing required cookie"):
        CookieAuth.from_cookies({"uid": "abc"})

def test_cookie_auth_from_storage(tmp_path: Path):
    cookie_file = tmp_path / "cookies.json"
    cookie_file.write_text(json.dumps({"uid": "u1", "sid": "s1"}))
    auth = CookieAuth.from_storage(cookie_file)
    assert auth.uid == "u1"
    assert auth.sid == "s1"

def test_cookie_auth_from_storage_missing_file(tmp_path: Path):
    import pytest
    with pytest.raises(FileNotFoundError):
        CookieAuth.from_storage(tmp_path / "nonexistent.json")
