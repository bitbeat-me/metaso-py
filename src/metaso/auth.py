"""Authentication for the Metaso client."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ApiKeyAuth:
    api_key: str

    @property
    def header_value(self) -> str:
        return f"Bearer {self.api_key}"


@dataclass
class CookieAuth:
    uid: str
    sid: str
    raw_cookies: dict[str, str] | None = None

    @property
    def token(self) -> str:
        return f"{self.uid}-{self.sid}"

    @property
    def header_value(self) -> str:
        return f"Bearer {self.token}"

    @classmethod
    def from_cookies(cls, cookies: dict[str, str]) -> CookieAuth:
        missing = {"uid", "sid"} - set(cookies.keys())
        if missing:
            raise ValueError(f"Missing required cookie keys: {missing}")
        return cls(uid=cookies["uid"], sid=cookies["sid"], raw_cookies=cookies)

    @classmethod
    def from_storage(cls, path: Path) -> CookieAuth:
        if not path.exists():
            raise FileNotFoundError(
                f"Cookie file not found: {path}\nRun 'metaso login' to authenticate."
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_cookies(data)
