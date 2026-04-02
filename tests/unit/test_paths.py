from pathlib import Path
from metaso.paths import get_home_dir, get_profile_dir, get_cookie_path, get_config_path, resolve_profile

def test_get_home_dir_default(monkeypatch):
    monkeypatch.delenv("METASO_HOME", raising=False)
    home = get_home_dir()
    assert home.name == "metaso"

def test_get_home_dir_from_env(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("METASO_HOME", str(tmp_path / "custom"))
    assert get_home_dir() == tmp_path / "custom"

def test_resolve_profile_default(monkeypatch):
    monkeypatch.delenv("METASO_PROFILE", raising=False)
    assert resolve_profile() == "default"

def test_resolve_profile_from_env(monkeypatch):
    monkeypatch.setenv("METASO_PROFILE", "work")
    assert resolve_profile() == "work"

def test_resolve_profile_explicit():
    assert resolve_profile("custom") == "custom"

def test_get_profile_dir(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("METASO_HOME", str(tmp_path))
    d = get_profile_dir("myprofile")
    assert d == tmp_path / "profiles" / "myprofile"

def test_get_cookie_path(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("METASO_HOME", str(tmp_path))
    p = get_cookie_path("default")
    assert p == tmp_path / "profiles" / "default" / "cookies.json"

def test_get_config_path(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("METASO_HOME", str(tmp_path))
    p = get_config_path()
    assert p == tmp_path / "config.json"

def test_path_traversal_blocked(monkeypatch, tmp_path: Path):
    import pytest
    monkeypatch.setenv("METASO_HOME", str(tmp_path))
    with pytest.raises(ValueError, match="Invalid profile name"):
        get_profile_dir("../../etc")
