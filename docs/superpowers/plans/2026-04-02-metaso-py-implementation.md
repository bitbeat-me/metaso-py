# metaso-py Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete Python client (SDK + CLI + skill) for Metaso AI search with dual-backend support (official API + reverse-engineered API).

**Architecture:** Layered design following notebooklm-py: CLI (click) → Client (MetasoClient + namespaced APIs) → Core (ClientCore + httpx) → Backend (ABC with official/unofficial implementations). Phased delivery: Phase 1 validates architecture with official backend + search, Phase 2 adds unofficial backend + full domain APIs, Phase 3 adds Claude Code skill.

**Tech Stack:** Python 3.10+, httpx, httpx-sse, click, pydantic v2, platformdirs, hatchling (build), pytest + respx (test), ruff + mypy (quality)

**Working Directory:** `/Users/caijie/Project/metaso/metaso-py`

**Review Protocol:** All review checkpoints use Codex CLI (`codex review` or `codex exec`).

---

## File Structure

```
src/metaso/
├── __init__.py              # Public exports: MetasoClient, types, exceptions
├── __main__.py              # python -m metaso entry point
├── client.py                # MetasoClient: async context manager, factory methods, namespaced APIs
├── auth.py                  # ApiKeyAuth, CookieAuth dataclasses
├── types.py                 # Pydantic models: SearchResult, SearchResponse, Topic, File, Book, UserInfo
├── exceptions.py            # MetasoError hierarchy
├── paths.py                 # Path resolution: get_home_dir, get_profile_dir, config/cookie paths
├── _core.py                 # ClientCore: httpx AsyncClient lifecycle, transport policy, request dispatch
├── _search.py               # SearchAPI: client.search namespace
├── _topics.py               # TopicsAPI: client.topics namespace [Phase 2]
├── _files.py                # FilesAPI: client.files namespace [Phase 2]
├── _bookshelf.py            # BookshelfAPI: client.bookshelf namespace [Phase 2]
├── _user.py                 # UserAPI: client.user namespace [Phase 2]
├── backends/
│   ├── __init__.py          # Re-exports BackendBase, OfficialBackend, UnofficialBackend
│   ├── base.py              # BackendBase ABC with capability model
│   ├── official.py          # OfficialBackend: API Key auth, /api/open/* endpoints
│   └── unofficial.py        # UnofficialBackend: uid-sid auth, reverse-engineered endpoints [Phase 2]
└── cli/
    ├── __init__.py           # Click group, sub-command registration
    ├── helpers.py            # resolve_client, async_command decorator, json output helper
    ├── session.py            # config, status commands; login/logout [Phase 2]
    ├── search.py             # metaso search command
    ├── topic.py              # metaso topic create/list/delete [Phase 2]
    ├── file.py               # metaso file upload/list/delete [Phase 2]
    ├── bookshelf.py          # metaso book add/list [Phase 2]
    ├── user.py               # metaso user info [Phase 2]
    └── skill.py              # metaso skill install [Phase 3]

tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_types.py
│   ├── test_exceptions.py
│   ├── test_auth.py
│   └── test_paths.py
├── integration/
│   ├── test_official_backend.py
│   ├── test_search_api.py
│   ├── test_client.py
│   └── test_cli.py
└── e2e/
    └── test_search_e2e.py

pyproject.toml
```

---

## Phase 1: Official Backend + Search

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/metaso/__init__.py`
- Create: `src/metaso/__main__.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "metaso-py"
version = "0.1.0"
description = "Python client for Metaso AI search"
requires-python = ">=3.10"
license = "MIT"
dependencies = [
    "httpx>=0.27",
    "httpx-sse>=0.4",
    "click>=8.0",
    "pydantic>=2.0",
    "platformdirs>=4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "respx>=0.21",
    "ruff>=0.4",
    "mypy>=1.10",
]

[project.scripts]
metaso = "metaso.cli:cli"

[tool.pytest.ini_options]
asyncio_mode = "auto"
markers = ["e2e: end-to-end tests requiring real API access"]

[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
```

- [ ] **Step 2: Create src/metaso/__init__.py**

```python
"""Metaso AI Search Python Client."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Create src/metaso/__main__.py**

```python
"""Allow running as python -m metaso."""

from metaso.cli import cli

cli()
```

- [ ] **Step 4: Create virtual environment and install**

Run: `cd /Users/caijie/Project/metaso/metaso-py && uv venv .venv && uv pip install -e ".[dev]"`
Expected: Successful install with all dependencies

- [ ] **Step 5: Verify installation**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/python -c "import metaso; print(metaso.__version__)"`
Expected: `0.1.0`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/metaso/__init__.py src/metaso/__main__.py
git commit -m "feat: project scaffolding with pyproject.toml"
```

---

### Task 2: Exceptions

**Files:**
- Create: `src/metaso/exceptions.py`
- Create: `tests/unit/test_exceptions.py`

- [ ] **Step 1: Write test**

```python
# tests/unit/test_exceptions.py
from metaso.exceptions import (
    MetasoError,
    AuthError,
    BackendError,
    NetworkError,
    RateLimitError,
    ServerError,
    NotFoundError,
    ValidationError,
)


def test_all_exceptions_inherit_from_metaso_error():
    for exc_cls in [AuthError, BackendError, NetworkError, RateLimitError, ServerError, NotFoundError, ValidationError]:
        assert issubclass(exc_cls, MetasoError)


def test_exception_message():
    err = AuthError("token expired")
    assert str(err) == "token expired"
    assert isinstance(err, MetasoError)


def test_backend_error_with_operation():
    err = BackendError("OfficialBackend does not support create_topic")
    assert "create_topic" in str(err)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/unit/test_exceptions.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement exceptions.py**

```python
# src/metaso/exceptions.py
"""Exception hierarchy for the Metaso client."""


class MetasoError(Exception):
    """Base exception for all metaso errors."""


class AuthError(MetasoError):
    """Authentication failed or expired."""


class BackendError(MetasoError):
    """Backend does not support this operation."""


class NetworkError(MetasoError):
    """Network connectivity issue."""


class RateLimitError(MetasoError):
    """Rate limit exceeded."""


class ServerError(MetasoError):
    """Server returned 5xx."""


class NotFoundError(MetasoError):
    """Resource not found."""


class ValidationError(MetasoError):
    """Invalid parameters."""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/unit/test_exceptions.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/metaso/exceptions.py tests/unit/test_exceptions.py
git commit -m "feat: exception hierarchy"
```

---

### Task 3: Data Types

**Files:**
- Create: `src/metaso/types.py`
- Create: `tests/unit/test_types.py`

- [ ] **Step 1: Write test**

```python
# tests/unit/test_types.py
from metaso.types import SearchResult, SearchResponse, Topic, File, Book, UserInfo


def test_search_result_creation():
    r = SearchResult(id="1", title="Test", url="https://example.com", snippet="hello", source="webpage")
    assert r.id == "1"
    assert r.source == "webpage"


def test_search_response_with_optional_fields():
    r = SearchResponse(query="test", results=[])
    assert r.summary is None
    assert r.session_id is None


def test_search_response_with_results():
    result = SearchResult(id="1", title="T", url="https://x.com", snippet="s", source="webpage")
    resp = SearchResponse(query="q", results=[result], summary="AI summary", session_id="sess-1")
    assert len(resp.results) == 1
    assert resp.summary == "AI summary"


def test_topic_minimal():
    t = Topic(id="t1", name="Research")
    assert t.dir_root_id is None


def test_file_defaults():
    f = File(id="f1", file_name="paper.pdf", parent_id="p1")
    assert f.progress == 0
    assert f.status == "processing"


def test_book_defaults():
    b = Book(id="b1", title="My Book", file_id="f1")
    assert b.progress == 0
    assert b.status == "processing"


def test_user_info_minimal():
    u = UserInfo(uid="u1")
    assert u.nickname is None
    assert u.vip_level == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/unit/test_types.py -v`
Expected: FAIL

- [ ] **Step 3: Implement types.py**

```python
# src/metaso/types.py
"""Data types for the Metaso client."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SearchResult:
    """A single search result item."""

    id: str
    title: str
    url: str
    snippet: str
    source: str  # "webpage", "scholar"


@dataclass
class SearchResponse:
    """Response from a search query."""

    query: str
    results: list[SearchResult]
    summary: str | None = None
    session_id: str | None = None


@dataclass
class Topic:
    """A knowledge base topic (collection of documents)."""

    id: str
    name: str
    dir_root_id: str | None = None
    created_at: datetime | None = None


@dataclass
class File:
    """A file uploaded to a topic."""

    id: str
    file_name: str
    parent_id: str
    progress: int = 0
    status: str = "processing"


@dataclass
class Book:
    """A book/PDF in the bookshelf."""

    id: str
    title: str
    file_id: str
    progress: int = 0
    status: str = "processing"


@dataclass
class UserInfo:
    """User account information."""

    uid: str
    nickname: str | None = None
    vip_level: int = 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/unit/test_types.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add src/metaso/types.py tests/unit/test_types.py
git commit -m "feat: data types (SearchResult, Topic, File, Book, UserInfo)"
```

---

### Task 4: Auth

**Files:**
- Create: `src/metaso/auth.py`
- Create: `tests/unit/test_auth.py`

- [ ] **Step 1: Write test**

```python
# tests/unit/test_auth.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/unit/test_auth.py -v`
Expected: FAIL

- [ ] **Step 3: Implement auth.py**

```python
# src/metaso/auth.py
"""Authentication for the Metaso client."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ApiKeyAuth:
    """Official API key authentication."""

    api_key: str

    @property
    def header_value(self) -> str:
        return f"Bearer {self.api_key}"


@dataclass
class CookieAuth:
    """Cookie-based authentication (uid + sid from browser)."""

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
        """Create from a cookie dict. Requires 'uid' and 'sid' keys."""
        missing = {"uid", "sid"} - set(cookies.keys())
        if missing:
            raise ValueError(f"Missing required cookie keys: {missing}")
        return cls(uid=cookies["uid"], sid=cookies["sid"], raw_cookies=cookies)

    @classmethod
    def from_storage(cls, path: Path) -> CookieAuth:
        """Load from a cookies.json file."""
        if not path.exists():
            raise FileNotFoundError(
                f"Cookie file not found: {path}\n"
                "Run 'metaso login' to authenticate."
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_cookies(data)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/unit/test_auth.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/metaso/auth.py tests/unit/test_auth.py
git commit -m "feat: dual auth (ApiKeyAuth + CookieAuth)"
```

---

### Task 5: Path Management

**Files:**
- Create: `src/metaso/paths.py`
- Create: `tests/unit/test_paths.py`

- [ ] **Step 1: Write test**

```python
# tests/unit/test_paths.py
import os
from pathlib import Path

from metaso.paths import get_home_dir, get_profile_dir, get_cookie_path, get_config_path, resolve_profile


def test_get_home_dir_default(monkeypatch):
    monkeypatch.delenv("METASO_HOME", raising=False)
    home = get_home_dir()
    # platformdirs returns platform-specific path; just check it ends with 'metaso'
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/unit/test_paths.py -v`
Expected: FAIL

- [ ] **Step 3: Implement paths.py**

```python
# src/metaso/paths.py
"""Path resolution for Metaso configuration files."""

from __future__ import annotations

import os
from pathlib import Path

from platformdirs import user_config_dir


def get_home_dir(create: bool = False) -> Path:
    """Get Metaso home directory.

    Precedence: METASO_HOME env var > platform-specific config dir.
    """
    if home := os.environ.get("METASO_HOME"):
        path = Path(home).expanduser().resolve()
    else:
        path = Path(user_config_dir("metaso"))

    if create:
        path.mkdir(parents=True, exist_ok=True)

    return path


def resolve_profile(profile: str | None = None) -> str:
    """Resolve the active profile name.

    Precedence: explicit arg > METASO_PROFILE env > "default".
    """
    if profile:
        return profile
    if env_profile := os.environ.get("METASO_PROFILE"):
        return env_profile
    return "default"


def get_profile_dir(profile: str | None = None, create: bool = False) -> Path:
    """Get directory for a specific profile."""
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
    """Get cookies.json path for a profile."""
    return get_profile_dir(profile) / "cookies.json"


def get_config_path() -> Path:
    """Get global config.json path."""
    return get_home_dir() / "config.json"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/unit/test_paths.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add src/metaso/paths.py tests/unit/test_paths.py
git commit -m "feat: path management with platformdirs"
```

---

### Task 6: Backend Base + Official Backend

**Files:**
- Create: `src/metaso/backends/__init__.py`
- Create: `src/metaso/backends/base.py`
- Create: `src/metaso/backends/official.py`
- Create: `tests/integration/test_official_backend.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write test**

```python
# tests/conftest.py
import pytest


def pytest_collection_modifyitems(config, items):
    """Skip e2e tests unless --run-e2e is passed."""
    if not config.getoption("--run-e2e", default=False):
        skip_e2e = pytest.mark.skip(reason="need --run-e2e option to run")
        for item in items:
            if "e2e" in item.keywords:
                item.add_marker(skip_e2e)


def pytest_addoption(parser):
    parser.addoption("--run-e2e", action="store_true", default=False, help="run e2e tests")
```

```python
# tests/integration/test_official_backend.py
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
        "items": [
            {
                "id": "r1",
                "title": "AI Trends 2026",
                "url": "https://example.com/ai",
                "snippet": "Artificial intelligence is...",
                "source": "webpage",
            }
        ],
        "sessionId": "sess-abc",
    },
}


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
    assert result.query == "AI trends"
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

    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer sk-test"


@respx.mock
@pytest.mark.asyncio
async def test_search_with_mode(backend):
    route = respx.post("https://metaso.cn/api/open/search/v2").mock(
        return_value=httpx.Response(200, json=SEARCH_RESPONSE_JSON)
    )
    async with httpx.AsyncClient() as http_client:
        backend._http_client = http_client
        await backend.search("test", mode="research")

    import json
    body = json.loads(route.calls.last.request.content)
    # Mode is not sent to official API (it uses different endpoint params)
    assert body["question"] == "test"


def test_capabilities(backend):
    caps = backend.capabilities()
    assert "search" in caps


def test_supports(backend):
    assert backend.supports("search") is True
    assert backend.supports("create_topic") is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/integration/test_official_backend.py -v`
Expected: FAIL

- [ ] **Step 3: Implement backends**

```python
# src/metaso/backends/__init__.py
"""Backend implementations for the Metaso client."""

from .base import BackendBase
from .official import OfficialBackend

__all__ = ["BackendBase", "OfficialBackend"]
```

```python
# src/metaso/backends/base.py
"""Abstract backend base class with capability model."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from pathlib import Path

from metaso.exceptions import BackendError
from metaso.types import Book, File, SearchResponse, Topic, UserInfo


class BackendBase(ABC):
    """Abstract base for Metaso API backends."""

    @abstractmethod
    def capabilities(self) -> set[str]:
        """Return set of supported operation names."""

    def supports(self, operation: str) -> bool:
        """Check if this backend supports a given operation."""
        return operation in self.capabilities()

    @abstractmethod
    async def search(
        self,
        query: str,
        mode: str = "concise",
        stream: bool = False,
        session_id: str | None = None,
        **kwargs,
    ) -> SearchResponse | AsyncIterator[dict]:
        """Execute a search query."""

    async def create_topic(self, name: str) -> Topic:
        raise BackendError(f"{self.__class__.__name__} does not support create_topic")

    async def list_topics(self) -> list[Topic]:
        raise BackendError(f"{self.__class__.__name__} does not support list_topics")

    async def delete_topic(self, topic_id: str) -> bool:
        raise BackendError(f"{self.__class__.__name__} does not support delete_topic")

    async def upload_file(self, topic_id: str, file_path: Path) -> File:
        raise BackendError(f"{self.__class__.__name__} does not support upload_file")

    async def list_files(self, topic_id: str) -> list[File]:
        raise BackendError(f"{self.__class__.__name__} does not support list_files")

    async def delete_file(self, file_id: str) -> bool:
        raise BackendError(f"{self.__class__.__name__} does not support delete_file")

    async def add_book(self, topic_id: str, url: str) -> Book:
        raise BackendError(f"{self.__class__.__name__} does not support add_book")

    async def list_books(self, topic_id: str) -> list[Book]:
        raise BackendError(f"{self.__class__.__name__} does not support list_books")

    async def user_info(self) -> UserInfo:
        raise BackendError(f"{self.__class__.__name__} does not support user_info")
```

```python
# src/metaso/backends/official.py
"""Official API backend using API key authentication."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path

import httpx

from metaso.auth import ApiKeyAuth
from metaso.exceptions import AuthError, NetworkError, RateLimitError, ServerError
from metaso.types import Book, File, SearchResponse, SearchResult, Topic, UserInfo

from .base import BackendBase

BASE_URL = "https://metaso.cn/api/open"


class OfficialBackend(BackendBase):
    """Backend using the official Metaso API with API key auth."""

    def __init__(self, auth: ApiKeyAuth, base_url: str = BASE_URL):
        self._auth = auth
        self._base_url = base_url.rstrip("/")
        self._http_client: httpx.AsyncClient | None = None

    def capabilities(self) -> set[str]:
        return {
            "search",
            "create_topic",
            "list_topics",
            "delete_topic",
            "upload_file",
            "list_files",
            "delete_file",
            "add_book",
            "list_books",
        }

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": self._auth.header_value,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            raise RuntimeError("Backend not connected. Use within async context manager.")
        return self._http_client

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make an authenticated request with error handling."""
        client = self._get_client()
        url = f"{self._base_url}{path}"
        try:
            response = await client.request(method, url, headers=self._headers(), **kwargs)
        except httpx.HTTPError as exc:
            raise NetworkError(f"Request failed: {exc}") from exc

        if response.status_code == 401:
            raise AuthError("Invalid API key. Check your METASO_API_KEY.")
        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded. Try again later.")
        if response.status_code >= 500:
            raise ServerError(f"Server error {response.status_code}: {response.text}")
        response.raise_for_status()
        return response

    async def search(
        self,
        query: str,
        mode: str = "concise",
        stream: bool = False,
        session_id: str | None = None,
        **kwargs,
    ) -> SearchResponse | AsyncIterator[dict]:
        payload = {
            "question": query,
            "lang": kwargs.get("lang", "zh"),
            "stream": stream,
        }
        if session_id:
            payload["sessionId"] = session_id

        if stream:
            return self._search_stream(payload)

        response = await self._request("POST", "/search/v2", json=payload)
        data = response.json()
        return self._parse_search_response(query, data)

    async def _search_stream(self, payload: dict) -> AsyncIterator[dict]:
        """Stream search results via SSE."""
        client = self._get_client()
        url = f"{self._base_url}/search/v2"
        from httpx_sse import aconnect_sse

        async with aconnect_sse(client, "POST", url, json=payload, headers=self._headers()) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.data == "[DONE]":
                    break
                yield json.loads(sse.data)

    def _parse_search_response(self, query: str, data: dict) -> SearchResponse:
        """Parse official API response into SearchResponse."""
        inner = data.get("data", data)
        items = inner.get("items", [])
        results = [
            SearchResult(
                id=item.get("id", ""),
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("snippet", ""),
                source=item.get("source", "webpage"),
            )
            for item in items
        ]
        return SearchResponse(
            query=query,
            results=results,
            summary=inner.get("summary"),
            session_id=inner.get("sessionId"),
        )

    async def create_topic(self, name: str) -> Topic:
        response = await self._request("PUT", "/topic", json={"name": name})
        data = response.json()["data"]
        return Topic(
            id=data["id"],
            name=data["name"],
            dir_root_id=data.get("dirRootId"),
        )

    async def list_topics(self) -> list[Topic]:
        response = await self._request("GET", "/topics")
        items = response.json().get("data", [])
        return [
            Topic(id=t["id"], name=t["name"], dir_root_id=t.get("dirRootId"))
            for t in items
        ]

    async def delete_topic(self, topic_id: str) -> bool:
        response = await self._request("POST", "/topic/trash", json={"ids": [topic_id]})
        return response.json().get("errCode") == 0

    async def upload_file(self, topic_id: str, file_path: Path) -> File:
        with open(file_path, "rb") as f:
            response = await self._request(
                "PUT",
                f"/file/{topic_id}",
                files={"file": f},
                headers={"Authorization": self._auth.header_value},
            )
        data = response.json()["data"][0]
        return File(
            id=data["id"],
            file_name=data["fileName"],
            parent_id=data["parentId"],
            progress=data.get("progress", 0),
        )

    async def list_files(self, topic_id: str) -> list[File]:
        response = await self._request("GET", f"/file/{topic_id}/list")
        items = response.json().get("data", [])
        return [
            File(
                id=f["id"],
                file_name=f["fileName"],
                parent_id=f["parentId"],
                progress=f.get("progress", 0),
            )
            for f in items
        ]

    async def delete_file(self, file_id: str) -> bool:
        response = await self._request("POST", "/file/trash", json={"ids": [file_id]})
        return response.json().get("errCode") == 0

    async def add_book(self, topic_id: str, url: str) -> Book:
        response = await self._request("POST", "/bookshelf/add", json={"topicId": topic_id, "url": url})
        data = response.json()["data"]
        return Book(
            id=data["id"],
            title=data["title"],
            file_id=data["fileId"],
            progress=data.get("progress", 0),
        )

    async def list_books(self, topic_id: str) -> list[Book]:
        response = await self._request("GET", f"/bookshelf/{topic_id}/list")
        items = response.json().get("data", [])
        return [
            Book(id=b["id"], title=b["title"], file_id=b["fileId"], progress=b.get("progress", 0))
            for b in items
        ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/integration/test_official_backend.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/metaso/backends/ tests/conftest.py tests/integration/test_official_backend.py
git commit -m "feat: backend abstraction + official backend implementation"
```

---

### Task 7: ClientCore

**Files:**
- Create: `src/metaso/_core.py`

- [ ] **Step 1: Implement _core.py**

```python
# src/metaso/_core.py
"""Core infrastructure for the Metaso client."""

from __future__ import annotations

import logging

import httpx

from metaso.backends.base import BackendBase

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0
DEFAULT_CONNECT_TIMEOUT = 10.0
USER_AGENT = "metaso-py/0.1.0"


class ClientCore:
    """Manages httpx client lifecycle and backend dispatch."""

    def __init__(self, backend: BackendBase, timeout: float = DEFAULT_TIMEOUT):
        self._backend = backend
        self._timeout = timeout
        self._http_client: httpx.AsyncClient | None = None

    @property
    def backend(self) -> BackendBase:
        return self._backend

    @property
    def is_open(self) -> bool:
        return self._http_client is not None and not self._http_client.is_closed

    async def open(self) -> None:
        """Open the HTTP client and inject it into the backend."""
        if self._http_client is not None:
            return
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout, connect=DEFAULT_CONNECT_TIMEOUT),
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )
        self._backend._http_client = self._http_client
        logger.debug("ClientCore opened")

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None
            self._backend._http_client = None
            logger.debug("ClientCore closed")
```

- [ ] **Step 2: Commit**

```bash
git add src/metaso/_core.py
git commit -m "feat: ClientCore with httpx lifecycle management"
```

---

### Task 8: SearchAPI + MetasoClient

**Files:**
- Create: `src/metaso/_search.py`
- Create: `src/metaso/client.py`
- Create: `tests/integration/test_search_api.py`
- Create: `tests/integration/test_client.py`

- [ ] **Step 1: Write tests**

```python
# tests/integration/test_search_api.py
import httpx
import pytest
import respx

from metaso.auth import ApiKeyAuth
from metaso.backends.official import OfficialBackend
from metaso._core import ClientCore
from metaso._search import SearchAPI
from metaso.types import SearchResponse

SEARCH_RESPONSE = {
    "errCode": 0,
    "data": {
        "items": [{"id": "1", "title": "T", "url": "https://x.com", "snippet": "s", "source": "webpage"}],
        "sessionId": "s1",
    },
}


@respx.mock
@pytest.mark.asyncio
async def test_search_api_query():
    respx.post("https://metaso.cn/api/open/search/v2").mock(
        return_value=httpx.Response(200, json=SEARCH_RESPONSE)
    )
    auth = ApiKeyAuth(api_key="sk-test")
    backend = OfficialBackend(auth=auth)
    core = ClientCore(backend)
    search = SearchAPI(core)

    await core.open()
    try:
        result = await search.query("test")
        assert isinstance(result, SearchResponse)
        assert result.query == "test"
        assert len(result.results) == 1
    finally:
        await core.close()
```

```python
# tests/integration/test_client.py
import httpx
import os
import pytest
import respx

from metaso.client import MetasoClient

SEARCH_RESPONSE = {
    "errCode": 0,
    "data": {
        "items": [{"id": "1", "title": "T", "url": "https://x.com", "snippet": "s", "source": "webpage"}],
        "sessionId": "s1",
    },
}


@respx.mock
@pytest.mark.asyncio
async def test_client_from_api_key():
    respx.post("https://metaso.cn/api/open/search/v2").mock(
        return_value=httpx.Response(200, json=SEARCH_RESPONSE)
    )
    async with MetasoClient.from_api_key("sk-test") as client:
        result = await client.search.query("test")
        assert result.query == "test"


@respx.mock
@pytest.mark.asyncio
async def test_client_auto_with_env(monkeypatch):
    monkeypatch.setenv("METASO_API_KEY", "sk-env")
    respx.post("https://metaso.cn/api/open/search/v2").mock(
        return_value=httpx.Response(200, json=SEARCH_RESPONSE)
    )
    async with MetasoClient.auto() as client:
        result = await client.search.query("test")
        assert result.query == "test"


@pytest.mark.asyncio
async def test_client_auto_no_credentials(monkeypatch, tmp_path):
    monkeypatch.delenv("METASO_API_KEY", raising=False)
    monkeypatch.setenv("METASO_HOME", str(tmp_path))
    with pytest.raises(ValueError, match="No credentials found"):
        MetasoClient.auto()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/integration/test_search_api.py tests/integration/test_client.py -v`
Expected: FAIL

- [ ] **Step 3: Implement _search.py**

```python
# src/metaso/_search.py
"""Search API namespace for the Metaso client."""

from __future__ import annotations

from collections.abc import AsyncIterator

from metaso._core import ClientCore
from metaso.types import SearchResponse


class SearchAPI:
    """Provides search operations via client.search namespace."""

    def __init__(self, core: ClientCore):
        self._core = core

    async def query(
        self,
        question: str,
        mode: str = "concise",
        stream: bool = False,
        session_id: str | None = None,
        **kwargs,
    ) -> SearchResponse | AsyncIterator[dict]:
        """Execute a search query.

        Args:
            question: The search query string.
            mode: Search mode - "concise", "detail", "research", "scholar".
            stream: If True, return an async iterator of SSE events.
            session_id: For multi-turn conversations.

        Returns:
            SearchResponse for non-streaming, AsyncIterator[dict] for streaming.
        """
        return await self._core.backend.search(
            query=question, mode=mode, stream=stream, session_id=session_id, **kwargs
        )
```

- [ ] **Step 4: Implement client.py**

```python
# src/metaso/client.py
"""MetasoClient - main entry point for the Metaso Python client."""

from __future__ import annotations

import logging
import os

from metaso._core import ClientCore, DEFAULT_TIMEOUT
from metaso._search import SearchAPI
from metaso.auth import ApiKeyAuth, CookieAuth
from metaso.backends.official import OfficialBackend
from metaso.paths import get_cookie_path

logger = logging.getLogger(__name__)


class MetasoClient:
    """Async client for the Metaso AI search API.

    Provides search and knowledge management through namespaced sub-APIs:
    - search: Execute search queries

    Usage:
        async with MetasoClient.from_api_key("sk-xxx") as client:
            result = await client.search.query("AI trends")
    """

    def __init__(self, backend, timeout: float = DEFAULT_TIMEOUT):
        self._core = ClientCore(backend, timeout=timeout)
        self.search = SearchAPI(self._core)

    async def __aenter__(self) -> MetasoClient:
        await self._core.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._core.close()

    @property
    def is_connected(self) -> bool:
        return self._core.is_open

    @classmethod
    def from_api_key(cls, api_key: str, **kwargs) -> MetasoClient:
        """Create client with official API backend."""
        auth = ApiKeyAuth(api_key=api_key)
        backend = OfficialBackend(auth=auth)
        return cls(backend, **kwargs)

    @classmethod
    def from_storage(cls, profile: str | None = None, **kwargs) -> MetasoClient:
        """Create client with unofficial backend from stored cookies."""
        cookie_path = get_cookie_path(profile)
        auth = CookieAuth.from_storage(cookie_path)
        # Phase 2: will use UnofficialBackend
        # For now, raise informative error
        raise NotImplementedError(
            "Unofficial backend not yet implemented. Use MetasoClient.from_api_key() "
            "or set METASO_API_KEY environment variable."
        )

    @classmethod
    def auto(cls, **kwargs) -> MetasoClient:
        """Auto-select backend: prefer METASO_API_KEY, fallback to stored cookies."""
        api_key = os.environ.get("METASO_API_KEY")
        if api_key:
            return cls.from_api_key(api_key, **kwargs)

        try:
            return cls.from_storage(**kwargs)
        except (FileNotFoundError, NotImplementedError):
            raise ValueError(
                "No credentials found. Either:\n"
                "  1. Set METASO_API_KEY environment variable, or\n"
                "  2. Run 'metaso login' to authenticate via browser."
            )
```

- [ ] **Step 5: Update __init__.py exports**

```python
# src/metaso/__init__.py
"""Metaso AI Search Python Client."""

__version__ = "0.1.0"

from metaso.client import MetasoClient
from metaso.types import Book, File, SearchResponse, SearchResult, Topic, UserInfo
from metaso.exceptions import (
    AuthError,
    BackendError,
    MetasoError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)

__all__ = [
    "MetasoClient",
    "SearchResult",
    "SearchResponse",
    "Topic",
    "File",
    "Book",
    "UserInfo",
    "MetasoError",
    "AuthError",
    "BackendError",
    "NetworkError",
    "RateLimitError",
    "ServerError",
    "NotFoundError",
    "ValidationError",
]
```

- [ ] **Step 6: Run tests**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/ -v`
Expected: All passed

- [ ] **Step 7: Commit**

```bash
git add src/metaso/_search.py src/metaso/client.py src/metaso/__init__.py tests/integration/test_search_api.py tests/integration/test_client.py
git commit -m "feat: SearchAPI + MetasoClient with factory methods"
```

---

### Task 9: CLI Foundation + Search Command

**Files:**
- Create: `src/metaso/cli/__init__.py`
- Create: `src/metaso/cli/helpers.py`
- Create: `src/metaso/cli/session.py`
- Create: `src/metaso/cli/search.py`
- Create: `tests/integration/test_cli.py`

- [ ] **Step 1: Write test**

```python
# tests/integration/test_cli.py
import httpx
import pytest
import respx
from click.testing import CliRunner

from metaso.cli import cli

SEARCH_RESPONSE = {
    "errCode": 0,
    "data": {
        "items": [{"id": "1", "title": "AI Result", "url": "https://x.com", "snippet": "test", "source": "webpage"}],
        "sessionId": "s1",
    },
}


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
    assert len(data["results"]) == 1


def test_status_no_credentials(monkeypatch, tmp_path):
    monkeypatch.delenv("METASO_API_KEY", raising=False)
    monkeypatch.setenv("METASO_HOME", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "not configured" in result.output.lower() or "No" in result.output


def test_config_set_api_key(monkeypatch, tmp_path):
    monkeypatch.setenv("METASO_HOME", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "set", "api-key", "sk-new"])
    assert result.exit_code == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/integration/test_cli.py -v`
Expected: FAIL

- [ ] **Step 3: Implement CLI**

```python
# src/metaso/cli/__init__.py
"""Metaso CLI - command line interface for Metaso AI search."""

import click

from metaso.cli.session import config_group, status_cmd
from metaso.cli.search import search_cmd


@click.group()
@click.version_option(package_name="metaso-py")
@click.option("--profile", default=None, help="Profile name for multi-account support.")
@click.pass_context
def cli(ctx, profile):
    """Metaso AI Search - Python client."""
    ctx.ensure_object(dict)
    ctx.obj["profile"] = profile


cli.add_command(search_cmd, "search")
cli.add_command(status_cmd, "status")
cli.add_command(config_group, "config")
```

```python
# src/metaso/cli/helpers.py
"""Shared CLI utilities."""

from __future__ import annotations

import asyncio
import functools
import json
import sys
from dataclasses import asdict
from typing import Any

import click

from metaso.client import MetasoClient


def async_command(f):
    """Decorator to run async click commands."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def get_client(ctx: click.Context) -> MetasoClient:
    """Create a MetasoClient from CLI context."""
    profile = ctx.obj.get("profile")
    return MetasoClient.auto(profile=profile) if profile else MetasoClient.auto()


def output_json(data: Any) -> None:
    """Print data as formatted JSON."""
    if hasattr(data, "__dataclass_fields__"):
        data = asdict(data)
    click.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def output_text(text: str) -> None:
    """Print text output."""
    click.echo(text)
```

```python
# src/metaso/cli/session.py
"""Session management commands: config, status."""

from __future__ import annotations

import json
import os

import click

from metaso.paths import get_config_path, get_home_dir


@click.command("status")
@click.pass_context
def status_cmd(ctx):
    """Show authentication status and active configuration."""
    api_key = os.environ.get("METASO_API_KEY")
    profile = ctx.obj.get("profile", "default") or "default"

    click.echo(f"Profile: {profile}")

    if api_key:
        masked = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
        click.echo(f"API Key: {masked}")
        click.echo(f"Backend: official")
    else:
        click.echo("API Key: not configured")

    config_path = get_config_path()
    if config_path.exists():
        click.echo(f"Config: {config_path}")
    else:
        click.echo(f"Config: {config_path} (not created yet)")


@click.group("config")
def config_group():
    """Manage Metaso configuration."""


@config_group.command("set")
@click.argument("key", type=click.Choice(["api-key", "backend"]))
@click.argument("value")
@click.pass_context
def config_set(ctx, key, value):
    """Set a configuration value."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config = {}
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))

    if key == "api-key":
        config["api_key"] = value
        click.echo(f"API key saved to {config_path}")
    elif key == "backend":
        if value not in ("official", "unofficial", "auto"):
            raise click.BadParameter("Must be one of: official, unofficial, auto")
        config["backend"] = value
        click.echo(f"Backend set to: {value}")

    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
```

```python
# src/metaso/cli/search.py
"""Search command for the Metaso CLI."""

from __future__ import annotations

from dataclasses import asdict

import click

from metaso.cli.helpers import async_command, get_client, output_json, output_text


@click.command("search")
@click.argument("query")
@click.option("--mode", "-m", default="concise", type=click.Choice(["concise", "detail", "research", "scholar"]),
              help="Search mode.")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON.")
@click.option("--stream", is_flag=True, help="Stream results via SSE.")
@click.pass_context
@async_command
async def search_cmd(ctx, query, mode, json_output, stream):
    """Search Metaso AI."""
    client = get_client(ctx)
    async with client:
        if stream:
            async for chunk in await client.search.query(query, mode=mode, stream=True):
                if json_output:
                    output_json(chunk)
                else:
                    text = chunk.get("text", chunk.get("data", ""))
                    if text:
                        click.echo(text, nl=False)
            click.echo()
        else:
            result = await client.search.query(query, mode=mode)
            if json_output:
                output_json(asdict(result))
            else:
                if result.summary:
                    click.echo(f"\n{result.summary}\n")
                click.echo(f"Found {len(result.results)} results:\n")
                for i, r in enumerate(result.results, 1):
                    click.echo(f"  {i}. {r.title}")
                    click.echo(f"     {r.url}")
                    click.echo(f"     {r.snippet[:100]}...")
                    click.echo()
```

- [ ] **Step 4: Run tests**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/integration/test_cli.py -v`
Expected: 4 passed

- [ ] **Step 5: Run all tests**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/ -v`
Expected: All passed

- [ ] **Step 6: Run quality checks**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/ruff format src/ tests/ && .venv/bin/ruff check src/ tests/`
Expected: No errors

- [ ] **Step 7: Commit**

```bash
git add src/metaso/cli/ tests/integration/test_cli.py
git commit -m "feat: CLI with search command, status, and config"
```

---

### Task 10: Phase 1 Review Checkpoint

**Review with Codex. GATE: must PASS before proceeding to Phase 2.**

- [ ] **Step 1: Run full test suite**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/ -v --tb=short`

- [ ] **Step 2: Run quality checks**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/ruff format src/ tests/ && .venv/bin/ruff check src/ tests/ && .venv/bin/mypy src/metaso --ignore-missing-imports`

- [ ] **Step 3: Codex review**

Run: `cd /Users/caijie/Project/metaso/metaso-py && codex review --base main -c 'model_reasoning_effort="high"' --enable web_search_cached`

If FAIL: fix issues and re-run. If PASS: proceed to Phase 2.

---

## Phase 2: Unofficial Backend + Full Domain APIs

### Task 11: Unofficial Backend

**Files:**
- Create: `src/metaso/backends/unofficial.py`
- Create: `tests/integration/test_unofficial_backend.py`

- [ ] **Step 1: Write test**

```python
# tests/integration/test_unofficial_backend.py
import httpx
import pytest
import respx

from metaso.auth import CookieAuth
from metaso.backends.unofficial import UnofficialBackend
from metaso.types import SearchResponse

META_TOKEN_HTML = '<html><meta id="meta-token" content="test-meta-token-123"></html>'

SEARCH_RESPONSE = {
    "data": {
        "id": "conv1",
    },
}


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
    respx.get("https://metaso.cn/").mock(
        return_value=httpx.Response(200, text=META_TOKEN_HTML)
    )
    async with httpx.AsyncClient() as http_client:
        backend._http_client = http_client
        token = await backend._acquire_meta_token()
    assert token == "test-meta-token-123"


def test_generate_cookie(backend):
    cookie = backend._generate_cookie()
    assert cookie == "uid=test-uid; sid=test-sid"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/integration/test_unofficial_backend.py -v`
Expected: FAIL

- [ ] **Step 3: Implement unofficial.py**

```python
# src/metaso/backends/unofficial.py
"""Unofficial backend using reverse-engineered API with uid-sid cookie auth."""

from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator

import httpx

from metaso.auth import CookieAuth
from metaso.exceptions import AuthError, NetworkError, ServerError
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
    """Backend using reverse-engineered Metaso web API."""

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

    async def _create_session(self, question: str, mode: str) -> str:
        """Create a search session and return conversation ID."""
        meta_token = await self._ensure_meta_token()

        # Map mode to engine type
        engine_type = "web"
        if mode in ("scholar", "concise-scholar", "detail-scholar", "research-scholar"):
            engine_type = "scholar"

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
        return data["data"]["id"]

    async def search(
        self,
        query: str,
        mode: str = "concise",
        stream: bool = False,
        session_id: str | None = None,
        **kwargs,
    ) -> SearchResponse | AsyncIterator[dict]:
        """Execute search via unofficial API."""
        conv_id = session_id or await self._create_session(query, mode)

        if stream:
            return self._search_stream(query, conv_id)

        # For non-streaming, collect all SSE events
        chunks = []
        async for chunk in self._search_stream(query, conv_id):
            chunks.append(chunk)

        # Build response from collected chunks
        return SearchResponse(
            query=query,
            results=[],  # Unofficial API returns results inline in SSE
            summary=self._extract_summary(chunks),
            session_id=conv_id,
        )

    async def _search_stream(self, query: str, conv_id: str) -> AsyncIterator[dict]:
        """Stream search results via SSE from /api/searchV2."""
        meta_token = await self._ensure_meta_token()
        client = self._get_client()

        from httpx_sse import aconnect_sse

        async with aconnect_sse(
            client,
            "GET",
            f"{self._base_url}/api/searchV2",
            params={"sessionId": conv_id},
            headers={
                **FAKE_HEADERS,
                "Cookie": self._generate_cookie(),
                "Token": meta_token,
            },
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.data == "[DONE]":
                    break
                try:
                    yield json.loads(sse.data)
                except json.JSONDecodeError:
                    continue

    def _extract_summary(self, chunks: list[dict]) -> str | None:
        """Extract summary text from SSE chunks."""
        texts = []
        for chunk in chunks:
            if text := chunk.get("text", ""):
                texts.append(text)
        return "".join(texts) if texts else None
```

- [ ] **Step 4: Update backends/__init__.py**

```python
# src/metaso/backends/__init__.py
"""Backend implementations for the Metaso client."""

from .base import BackendBase
from .official import OfficialBackend
from .unofficial import UnofficialBackend

__all__ = ["BackendBase", "OfficialBackend", "UnofficialBackend"]
```

- [ ] **Step 5: Update client.py from_storage to use UnofficialBackend**

In `src/metaso/client.py`, replace the `from_storage` method body:

```python
    @classmethod
    def from_storage(cls, profile: str | None = None, **kwargs) -> MetasoClient:
        """Create client with unofficial backend from stored cookies."""
        cookie_path = get_cookie_path(profile)
        auth = CookieAuth.from_storage(cookie_path)
        from metaso.backends.unofficial import UnofficialBackend
        backend = UnofficialBackend(auth=auth)
        return cls(backend, **kwargs)
```

- [ ] **Step 6: Run tests**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/ -v`
Expected: All passed

- [ ] **Step 7: Commit**

```bash
git add src/metaso/backends/unofficial.py src/metaso/backends/__init__.py src/metaso/client.py tests/integration/test_unofficial_backend.py
git commit -m "feat: unofficial backend with uid-sid cookie auth"
```

---

### Task 12: Login Command (agent-browser)

**Files:**
- Modify: `src/metaso/cli/session.py`

- [ ] **Step 1: Add login command**

Add to `src/metaso/cli/session.py`:

```python
import subprocess
import time

@click.command("login")
@click.pass_context
def login_cmd(ctx):
    """Login to Metaso via browser (extracts cookies automatically)."""
    profile = ctx.obj.get("profile") or "default"

    click.echo("Opening Metaso in browser...")
    click.echo("Please complete login (phone number or WeChat scan).")
    click.echo()

    # Open metaso.cn
    subprocess.run(
        ["agent-browser", "open", "https://metaso.cn"],
        check=True, capture_output=True, text=True,
    )

    # Wait for network idle
    subprocess.run(
        ["agent-browser", "wait", "--load", "networkidle"],
        capture_output=True, text=True,
    )

    click.echo("Waiting for login... (press Ctrl+C to cancel)")
    click.echo()

    # Poll for cookies
    max_attempts = 60  # 5 minutes at 5s intervals
    for attempt in range(max_attempts):
        result = subprocess.run(
            ["agent-browser", "eval", "document.cookie"],
            capture_output=True, text=True,
        )
        cookie_str = result.stdout.strip()

        # Parse cookies
        cookies = {}
        for part in cookie_str.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                cookies[k.strip()] = v.strip()

        if "uid" in cookies and "sid" in cookies:
            # Save cookies
            from metaso.paths import get_profile_dir
            import json

            profile_dir = get_profile_dir(profile, create=True)
            cookie_file = profile_dir / "cookies.json"
            cookie_file.write_text(
                json.dumps({"uid": cookies["uid"], "sid": cookies["sid"]}, indent=2),
                encoding="utf-8",
            )

            # Close browser
            subprocess.run(["agent-browser", "close"], capture_output=True, text=True)

            click.echo(f"Login successful! Cookies saved to {cookie_file}")
            click.echo(f"  uid: {cookies['uid'][:8]}...")
            click.echo(f"  sid: {cookies['sid'][:8]}...")
            return

        time.sleep(5)

    # Timeout
    subprocess.run(["agent-browser", "close"], capture_output=True, text=True)
    click.echo("Login timed out. Please try again.", err=True)
    raise SystemExit(1)


@click.command("logout")
@click.pass_context
def logout_cmd(ctx):
    """Clear stored credentials."""
    profile = ctx.obj.get("profile") or "default"
    from metaso.paths import get_cookie_path
    cookie_path = get_cookie_path(profile)
    if cookie_path.exists():
        cookie_path.unlink()
        click.echo(f"Credentials cleared for profile '{profile}'.")
    else:
        click.echo(f"No credentials found for profile '{profile}'.")
```

- [ ] **Step 2: Register login/logout in cli/__init__.py**

Add to `src/metaso/cli/__init__.py`:

```python
from metaso.cli.session import config_group, status_cmd, login_cmd, logout_cmd

cli.add_command(login_cmd, "login")
cli.add_command(logout_cmd, "logout")
```

- [ ] **Step 3: Commit**

```bash
git add src/metaso/cli/session.py src/metaso/cli/__init__.py
git commit -m "feat: login/logout commands with agent-browser"
```

---

### Task 13: Domain APIs (Topics, Files, Bookshelf, User)

**Files:**
- Create: `src/metaso/_topics.py`
- Create: `src/metaso/_files.py`
- Create: `src/metaso/_bookshelf.py`
- Create: `src/metaso/_user.py`
- Modify: `src/metaso/client.py`

- [ ] **Step 1: Implement domain APIs**

```python
# src/metaso/_topics.py
"""Topics API namespace."""

from __future__ import annotations

from metaso._core import ClientCore
from metaso.types import Topic


class TopicsAPI:
    def __init__(self, core: ClientCore):
        self._core = core

    async def create(self, name: str) -> Topic:
        return await self._core.backend.create_topic(name)

    async def list(self) -> list[Topic]:
        return await self._core.backend.list_topics()

    async def delete(self, topic_id: str) -> bool:
        return await self._core.backend.delete_topic(topic_id)
```

```python
# src/metaso/_files.py
"""Files API namespace."""

from __future__ import annotations

from pathlib import Path

from metaso._core import ClientCore
from metaso.types import File


class FilesAPI:
    def __init__(self, core: ClientCore):
        self._core = core

    async def upload(self, topic_id: str, file_path: Path | str) -> File:
        return await self._core.backend.upload_file(topic_id, Path(file_path))

    async def list(self, topic_id: str) -> list[File]:
        return await self._core.backend.list_files(topic_id)

    async def delete(self, file_id: str) -> bool:
        return await self._core.backend.delete_file(file_id)
```

```python
# src/metaso/_bookshelf.py
"""Bookshelf API namespace."""

from __future__ import annotations

from metaso._core import ClientCore
from metaso.types import Book


class BookshelfAPI:
    def __init__(self, core: ClientCore):
        self._core = core

    async def add(self, topic_id: str, url: str) -> Book:
        return await self._core.backend.add_book(topic_id, url)

    async def list(self, topic_id: str) -> list[Book]:
        return await self._core.backend.list_books(topic_id)
```

```python
# src/metaso/_user.py
"""User API namespace."""

from __future__ import annotations

from metaso._core import ClientCore
from metaso.types import UserInfo


class UserAPI:
    def __init__(self, core: ClientCore):
        self._core = core

    async def info(self) -> UserInfo:
        return await self._core.backend.user_info()
```

- [ ] **Step 2: Update client.py to register all APIs**

Update `MetasoClient.__init__`:

```python
    def __init__(self, backend, timeout: float = DEFAULT_TIMEOUT):
        self._core = ClientCore(backend, timeout=timeout)
        self.search = SearchAPI(self._core)

        from metaso._topics import TopicsAPI
        from metaso._files import FilesAPI
        from metaso._bookshelf import BookshelfAPI
        from metaso._user import UserAPI

        self.topics = TopicsAPI(self._core)
        self.files = FilesAPI(self._core)
        self.bookshelf = BookshelfAPI(self._core)
        self.user = UserAPI(self._core)
```

- [ ] **Step 3: Run tests**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/ -v`
Expected: All passed

- [ ] **Step 4: Commit**

```bash
git add src/metaso/_topics.py src/metaso/_files.py src/metaso/_bookshelf.py src/metaso/_user.py src/metaso/client.py
git commit -m "feat: domain APIs (topics, files, bookshelf, user)"
```

---

### Task 14: Domain CLI Commands

**Files:**
- Create: `src/metaso/cli/topic.py`
- Create: `src/metaso/cli/file.py`
- Create: `src/metaso/cli/bookshelf.py`
- Create: `src/metaso/cli/user.py`
- Modify: `src/metaso/cli/__init__.py`

- [ ] **Step 1: Implement topic CLI**

```python
# src/metaso/cli/topic.py
"""Topic management commands."""

from __future__ import annotations

from dataclasses import asdict

import click

from metaso.cli.helpers import async_command, get_client, output_json


@click.group("topic")
def topic_group():
    """Manage knowledge base topics."""


@topic_group.command("create")
@click.argument("name")
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
@async_command
async def topic_create(ctx, name, json_output):
    """Create a new topic."""
    client = get_client(ctx)
    async with client:
        topic = await client.topics.create(name)
        if json_output:
            output_json(asdict(topic))
        else:
            click.echo(f"Created topic: {topic.name} (id: {topic.id})")


@topic_group.command("list")
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
@async_command
async def topic_list(ctx, json_output):
    """List all topics."""
    client = get_client(ctx)
    async with client:
        topics = await client.topics.list()
        if json_output:
            output_json({"topics": [asdict(t) for t in topics]})
        else:
            if not topics:
                click.echo("No topics found.")
            for t in topics:
                click.echo(f"  {t.id}  {t.name}")


@topic_group.command("delete")
@click.argument("topic_id")
@click.pass_context
@async_command
async def topic_delete(ctx, topic_id):
    """Delete a topic."""
    client = get_client(ctx)
    async with client:
        success = await client.topics.delete(topic_id)
        if success:
            click.echo(f"Deleted topic: {topic_id}")
        else:
            click.echo(f"Failed to delete topic: {topic_id}", err=True)
```

```python
# src/metaso/cli/file.py
"""File management commands."""

from __future__ import annotations

from dataclasses import asdict

import click

from metaso.cli.helpers import async_command, get_client, output_json


@click.group("file")
def file_group():
    """Manage files in topics."""


@file_group.command("upload")
@click.argument("path", type=click.Path(exists=True))
@click.option("--topic", required=True, help="Topic ID.")
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
@async_command
async def file_upload(ctx, path, topic, json_output):
    """Upload a file to a topic."""
    client = get_client(ctx)
    async with client:
        f = await client.files.upload(topic, path)
        if json_output:
            output_json(asdict(f))
        else:
            click.echo(f"Uploaded: {f.file_name} (id: {f.id})")


@file_group.command("list")
@click.option("--topic", required=True, help="Topic ID.")
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
@async_command
async def file_list(ctx, topic, json_output):
    """List files in a topic."""
    client = get_client(ctx)
    async with client:
        files = await client.files.list(topic)
        if json_output:
            output_json({"files": [asdict(f) for f in files]})
        else:
            if not files:
                click.echo("No files found.")
            for f in files:
                click.echo(f"  {f.id}  {f.file_name}  progress={f.progress}%")


@file_group.command("delete")
@click.argument("file_id")
@click.pass_context
@async_command
async def file_delete(ctx, file_id):
    """Delete a file."""
    client = get_client(ctx)
    async with client:
        success = await client.files.delete(file_id)
        click.echo(f"Deleted: {file_id}" if success else f"Failed to delete: {file_id}")
```

```python
# src/metaso/cli/bookshelf.py
"""Bookshelf commands."""

from __future__ import annotations

from dataclasses import asdict

import click

from metaso.cli.helpers import async_command, get_client, output_json


@click.group("book")
def book_group():
    """Manage bookshelf."""


@book_group.command("add")
@click.argument("url")
@click.option("--topic", required=True, help="Topic ID.")
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
@async_command
async def book_add(ctx, url, topic, json_output):
    """Add a book/PDF from URL."""
    client = get_client(ctx)
    async with client:
        book = await client.bookshelf.add(topic, url)
        if json_output:
            output_json(asdict(book))
        else:
            click.echo(f"Added: {book.title} (id: {book.id})")


@book_group.command("list")
@click.option("--topic", required=True, help="Topic ID.")
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
@async_command
async def book_list(ctx, topic, json_output):
    """List books in a topic."""
    client = get_client(ctx)
    async with client:
        books = await client.bookshelf.list(topic)
        if json_output:
            output_json({"books": [asdict(b) for b in books]})
        else:
            if not books:
                click.echo("No books found.")
            for b in books:
                click.echo(f"  {b.id}  {b.title}  progress={b.progress}%")
```

```python
# src/metaso/cli/user.py
"""User commands."""

from __future__ import annotations

from dataclasses import asdict

import click

from metaso.cli.helpers import async_command, get_client, output_json


@click.command("user")
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
@async_command
async def user_cmd(ctx, json_output):
    """Show user information."""
    client = get_client(ctx)
    async with client:
        info = await client.user.info()
        if json_output:
            output_json(asdict(info))
        else:
            click.echo(f"UID: {info.uid}")
            if info.nickname:
                click.echo(f"Nickname: {info.nickname}")
            click.echo(f"VIP Level: {info.vip_level}")
```

- [ ] **Step 2: Register commands in cli/__init__.py**

Update `src/metaso/cli/__init__.py` to add all commands:

```python
from metaso.cli.topic import topic_group
from metaso.cli.file import file_group
from metaso.cli.bookshelf import book_group
from metaso.cli.user import user_cmd

cli.add_command(topic_group, "topic")
cli.add_command(file_group, "file")
cli.add_command(book_group, "book")
cli.add_command(user_cmd, "user")
```

- [ ] **Step 3: Run tests**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/ -v`
Expected: All passed

- [ ] **Step 4: Commit**

```bash
git add src/metaso/cli/topic.py src/metaso/cli/file.py src/metaso/cli/bookshelf.py src/metaso/cli/user.py src/metaso/cli/__init__.py
git commit -m "feat: CLI commands for topic, file, bookshelf, user"
```

---

### Task 15: Phase 2 Review Checkpoint

- [ ] **Step 1: Run full test suite + quality**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/ -v && .venv/bin/ruff format src/ tests/ && .venv/bin/ruff check src/ tests/ && .venv/bin/mypy src/metaso --ignore-missing-imports`

- [ ] **Step 2: Codex review**

Run: `cd /Users/caijie/Project/metaso/metaso-py && codex review --base main -c 'model_reasoning_effort="high"' --enable web_search_cached`

If FAIL: fix and re-run. If PASS: proceed to Phase 3.

---

## Phase 3: Claude Code Skill

### Task 16: Skill Install Command

**Files:**
- Create: `src/metaso/cli/skill.py`
- Modify: `src/metaso/cli/__init__.py`

- [ ] **Step 1: Implement skill.py**

```python
# src/metaso/cli/skill.py
"""Skill installation command."""

from __future__ import annotations

import importlib.resources
from pathlib import Path

import click


SKILL_CONTENT = '''---
name: metaso
description: Metaso AI search - full programmatic access. Search web/academic sources, manage knowledge base topics, upload files. Activates on explicit /metaso or intent like "search for X on Metaso"
---

# Metaso AI Search

Python client for Metaso AI search with dual backend support (official API + browser-based auth).

## Prerequisites

```bash
pip install metaso-py
metaso status              # Check auth
metaso config set api-key <key>  # Set API key
# OR
metaso login               # Browser login (extracts cookies)
```

## Quick Reference

| Task | Command |
|------|---------|
| Check status | `metaso status` |
| Set API key | `metaso config set api-key <key>` |
| Browser login | `metaso login` |
| Search (concise) | `metaso search "query"` |
| Search (detail) | `metaso search "query" --mode detail` |
| Search (research) | `metaso search "query" --mode research` |
| Search (scholar) | `metaso search "query" --mode scholar` |
| Search (JSON) | `metaso search "query" --json` |
| Create topic | `metaso topic create "name" --json` |
| List topics | `metaso topic list --json` |
| Delete topic | `metaso topic delete <id>` |
| Upload file | `metaso file upload ./file.pdf --topic <id> --json` |
| List files | `metaso file list --topic <id> --json` |
| Add book | `metaso book add <url> --topic <id> --json` |
| User info | `metaso user --json` |

## Autonomy Rules

**Run automatically (no confirmation):**
- `metaso status` - check state
- `metaso search` - execute searches
- `metaso topic list` - list topics
- `metaso file list` - list files
- `metaso book list` - list books
- `metaso user` - user info

**Ask before running:**
- `metaso login` - opens browser
- `metaso logout` - clears credentials
- `metaso topic delete` - destructive
- `metaso file delete` - destructive
- `metaso file upload` - writes data
- `metaso book add` - writes data
- `metaso config set` - modifies config

## JSON Output

All commands support `--json` for structured output:

```json
// metaso search "AI" --json
{"query": "AI", "results": [{"id": "...", "title": "...", "url": "...", "snippet": "...", "source": "webpage"}], "summary": "...", "session_id": "..."}

// metaso topic list --json
{"topics": [{"id": "...", "name": "...", "dir_root_id": "..."}]}

// metaso status --json
{"profile": "default", "backend": "official", "authenticated": true}
```

## Error Handling

| Error | Action |
|-------|--------|
| "No credentials found" | Run `metaso config set api-key <key>` or `metaso login` |
| "Invalid API key" | Check METASO_API_KEY or re-set via `metaso config set api-key` |
| "meta-token not found" | Session expired, run `metaso login` |
| "Rate limit exceeded" | Wait and retry |
| "does not support" | Operation not available on current backend |

## Multi-Account

Use `--profile` for multiple accounts:
```bash
metaso --profile work config set api-key <key>
metaso --profile work search "query"
```
'''


@click.group("skill")
def skill_group():
    """Manage Claude Code skill."""


@skill_group.command("install")
def skill_install():
    """Install the Metaso Claude Code skill."""
    skill_dir = Path.home() / ".claude" / "skills" / "metaso"
    skill_dir.mkdir(parents=True, exist_ok=True)

    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(SKILL_CONTENT, encoding="utf-8")

    click.echo(f"Skill installed to {skill_path}")
    click.echo("Restart Claude Code to activate the /metaso skill.")
```

- [ ] **Step 2: Register in cli/__init__.py**

Add to `src/metaso/cli/__init__.py`:

```python
from metaso.cli.skill import skill_group
cli.add_command(skill_group, "skill")
```

- [ ] **Step 3: Test skill install**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/metaso skill install`
Expected: "Skill installed to ~/.claude/skills/metaso/SKILL.md"

- [ ] **Step 4: Commit**

```bash
git add src/metaso/cli/skill.py src/metaso/cli/__init__.py
git commit -m "feat: skill install command for Claude Code integration"
```

---

### Task 17: Final Review + Polish

- [ ] **Step 1: Run full test suite**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/pytest tests/ -v`

- [ ] **Step 2: Run quality checks**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/ruff format src/ tests/ && .venv/bin/ruff check src/ tests/ && .venv/bin/mypy src/metaso --ignore-missing-imports`

- [ ] **Step 3: Verify CLI works end-to-end**

Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/metaso --help`
Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/metaso search --help`
Run: `cd /Users/caijie/Project/metaso/metaso-py && .venv/bin/metaso topic --help`

- [ ] **Step 4: Final Codex review**

Run: `cd /Users/caijie/Project/metaso/metaso-py && codex review --base main -c 'model_reasoning_effort="high"' --enable web_search_cached`

- [ ] **Step 5: Final commit if any fixes**

```bash
git add -A && git commit -m "chore: final polish from code review"
```
