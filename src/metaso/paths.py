"""Path resolution for Metaso configuration files."""

from __future__ import annotations

import os
from pathlib import Path

from platformdirs import user_config_dir


def get_home_dir(create: bool = False) -> Path:
    if home := os.environ.get("METASO_HOME"):
        path = Path(home).expanduser().resolve()
    else:
        path = Path(user_config_dir("metaso"))
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_profile(profile: str | None = None) -> str:
    if profile:
        return profile
    if env_profile := os.environ.get("METASO_PROFILE"):
        return env_profile
    return "default"


def get_profile_dir(profile: str | None = None, create: bool = False) -> Path:
    resolved = resolve_profile(profile)
    profiles_root = get_home_dir() / "profiles"
    path = (profiles_root / resolved).resolve()
    resolved_root = profiles_root.resolve()
    if not path.is_relative_to(resolved_root) or path == resolved_root:
        raise ValueError(f"Invalid profile name: {resolved!r}")
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_cookie_path(profile: str | None = None) -> Path:
    return get_profile_dir(profile) / "cookies.json"


def get_config_path() -> Path:
    return get_home_dir() / "config.json"
