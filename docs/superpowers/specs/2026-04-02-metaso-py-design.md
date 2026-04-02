# metaso-py Design Spec

Complete Python client (SDK + CLI + Claude Code skill) for Metaso AI search (https://metaso.cn).

## Architecture

Follows notebooklm-py's layered design with one structural difference: `backends/` replaces `rpc/` to support dual API backends.

```
CLI Layer (click)
    ↓
Client Layer (MetasoClient + namespaced sub-APIs)
    ↓
Core Layer (_core.py - ClientCore: httpx, transport policy, dispatch)
    ↓
Backend Layer (backends/)
    ├── official.py   (API Key → /api/open/*)
    └── unofficial.py (uid-sid cookies → reverse-engineered API)
```

## Phased Delivery

### Phase 1: Official Backend + Search (validate architecture)

- `client.py`, `_core.py`, `auth.py`, `types.py`, `exceptions.py`, `paths.py`
- `backends/base.py`, `backends/official.py`
- `_search.py` (single domain API)
- `cli/session.py` (config set api-key, status), `cli/search.py`
- Tests: unit + integration (respx fixtures)
- Build: pyproject.toml, uv + hatchling

### Phase 2: Unofficial Backend + Full Domain APIs

- `backends/unofficial.py` (uid-sid cookie auth, reverse-engineered endpoints)
- `cli/session.py` extended: `login` (agent-browser), `logout`
- `_topics.py`, `_files.py`, `_bookshelf.py`, `_user.py`
- `cli/topic.py`, `cli/file.py`, `cli/bookshelf.py`, `cli/user.py`
- Capability model: backend reports supported operations
- e2e tests (marked, separate from unit/integration)

### Phase 3: Claude Code Skill

- `SKILL.md` (command reference, autonomy rules, error handling)
- `cli/skill.py` (`metaso skill install`)

## Project Structure

```
src/metaso/
├── __init__.py              # Public exports
├── __main__.py              # python -m metaso
├── client.py                # MetasoClient
├── auth.py                  # ApiKeyAuth + CookieAuth
├── types.py                 # Pydantic dataclasses
├── exceptions.py            # Exception hierarchy
├── paths.py                 # Config/data path management
├── _core.py                 # ClientCore (httpx, transport, dispatch)
├── _search.py               # client.search (SearchAPI)
├── _topics.py               # client.topics (TopicsAPI) [Phase 2]
├── _files.py                # client.files (FilesAPI) [Phase 2]
├── _bookshelf.py            # client.bookshelf (BookshelfAPI) [Phase 2]
├── _user.py                 # client.user (UserAPI) [Phase 2]
├── backends/
│   ├── __init__.py
│   ├── base.py              # BackendBase (ABC + capability model)
│   ├── official.py          # OfficialBackend
│   └── unofficial.py        # UnofficialBackend [Phase 2]
└── cli/
    ├── __init__.py           # Click app
    ├── helpers.py            # Shared CLI utilities
    ├── session.py            # config, status, login [Phase 2], logout [Phase 2]
    ├── search.py             # search command
    ├── topic.py              # [Phase 2]
    ├── file.py               # [Phase 2]
    ├── bookshelf.py          # [Phase 2]
    ├── user.py               # [Phase 2]
    └── skill.py              # [Phase 3]

tests/
├── unit/                    # No network, encoding/decoding/types
├── integration/             # Mock HTTP (respx fixtures)
└── e2e/                     # Real API, marked @pytest.mark.e2e
```

## Client API

### Factory Methods

```python
class MetasoClient:
    def __init__(self, backend: BackendBase, timeout: float = 30.0): ...

    @classmethod
    def from_api_key(cls, api_key: str, **kwargs) -> "MetasoClient":
        """Create with official backend."""

    @classmethod
    def from_storage(cls, profile: str | None = None, **kwargs) -> "MetasoClient":
        """Create with unofficial backend, loading cookies from local storage."""

    @classmethod
    def auto(cls, **kwargs) -> "MetasoClient":
        """Auto-select: METASO_API_KEY env → official, else fallback to stored cookies."""

    async def __aenter__(self) -> "MetasoClient": ...
    async def __aexit__(self, *args): ...
```

### Namespaced Sub-APIs

```python
async with MetasoClient.from_api_key("sk-xxx") as client:
    # Search
    response = await client.search.query("AI trends", mode="concise")
    response = await client.search.query("AI trends", mode="research", stream=True)

    # Topics [Phase 2]
    topic = await client.topics.create("My Research")
    topics = await client.topics.list()
    await client.topics.delete(topic.id)

    # Files [Phase 2]
    file = await client.files.upload(topic.id, Path("paper.pdf"))
    files = await client.files.list(topic.id)

    # Bookshelf [Phase 2]
    book = await client.bookshelf.add(topic.id, "https://example.com/paper.pdf")
    books = await client.bookshelf.list(topic.id)

    # User [Phase 2]
    info = await client.user.info()
```

## Backend Abstraction

```python
class BackendBase(ABC):
    """Abstract backend with capability model."""

    @abstractmethod
    def capabilities(self) -> set[str]:
        """Return set of supported operation names."""

    def supports(self, operation: str) -> bool:
        return operation in self.capabilities()

    # Search (Phase 1)
    @abstractmethod
    async def search(self, query: str, mode: str = "concise",
                     stream: bool = False, session_id: str | None = None,
                     **kwargs) -> SearchResponse | AsyncIterator[dict]: ...

    # Topics (Phase 2)
    async def create_topic(self, name: str) -> Topic:
        raise BackendError(f"{self.__class__.__name__} does not support create_topic")

    async def list_topics(self) -> list[Topic]:
        raise BackendError(...)

    async def delete_topic(self, topic_id: str) -> bool:
        raise BackendError(...)

    # Files (Phase 2)
    async def upload_file(self, topic_id: str, file_path: Path) -> File:
        raise BackendError(...)

    async def list_files(self, topic_id: str) -> list[File]:
        raise BackendError(...)

    async def delete_file(self, file_id: str) -> bool:
        raise BackendError(...)

    # Bookshelf (Phase 2)
    async def add_book(self, topic_id: str, url: str) -> Book:
        raise BackendError(...)

    async def list_books(self, topic_id: str) -> list[Book]:
        raise BackendError(...)

    # User (Phase 2)
    async def user_info(self) -> UserInfo:
        raise BackendError(...)
```

Default implementations raise `BackendError` so backends only implement what they support.
CLI checks `backend.supports("operation")` to hide unavailable commands.

## Authentication

### Dual Auth Types

```python
@dataclass
class ApiKeyAuth:
    api_key: str
    # Used by: OfficialBackend
    # Header: Authorization: Bearer <api_key>

@dataclass
class CookieAuth:
    uid: str
    sid: str
    raw_cookies: dict[str, str] | None = None
    # Used by: UnofficialBackend
    # Header: Authorization: Bearer <uid>-<sid>

    @classmethod
    def from_storage(cls, profile: str | None = None) -> "CookieAuth":
        """Load from ~/.metaso/profiles/<profile>/cookies.json"""

    @property
    def token(self) -> str:
        return f"{self.uid}-{self.sid}"
```

### Login Flow (Phase 2)

Uses agent-browser to automate browser login:

1. `agent-browser open https://metaso.cn`
2. Print: "Please complete login in the browser (phone/WeChat scan)"
3. Poll cookies via `agent-browser eval` until `uid` and `sid` appear
4. Extract and save to `~/.metaso/profiles/<profile>/cookies.json`
5. Verify token validity via API call
6. `agent-browser close`

Fallback: manual cookie configuration via `metaso config set cookie <uid-sid>`.

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `METASO_API_KEY` | Official API key (used by `auto()`) |
| `METASO_HOME` | Custom config directory (default: platform-specific via platformdirs) |
| `METASO_PROFILE` | Override active profile name |

## Data Types

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SearchResult:
    id: str
    title: str
    url: str
    snippet: str
    source: str  # "webpage", "scholar"

@dataclass
class SearchResponse:
    query: str
    results: list[SearchResult]
    summary: str | None = None       # AI summary (research mode)
    session_id: str | None = None    # For multi-turn conversations

@dataclass
class Topic:
    id: str
    name: str
    dir_root_id: str | None = None
    created_at: datetime | None = None

@dataclass
class File:
    id: str
    file_name: str
    parent_id: str
    progress: int = 0
    status: str = "processing"

@dataclass
class Book:
    id: str
    title: str
    file_id: str
    progress: int = 0
    status: str = "processing"

@dataclass
class UserInfo:
    uid: str
    nickname: str | None = None
    vip_level: int = 0
```

## Exception Hierarchy

```python
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

## Transport Policy (_core.py)

```python
class ClientCore:
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_CONNECT_TIMEOUT = 10.0
    MAX_RETRIES = 3
    RETRY_BACKOFF = [1.0, 2.0, 4.0]  # Exponential backoff seconds

    # Retry on: 429 (rate limit), 500, 502, 503, 504
    # Do NOT retry on: 400, 401, 403, 404
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
```

- httpx.AsyncClient with configurable timeout
- Automatic retry with exponential backoff for transient errors
- Rate limit handling: respect Retry-After header when present
- User-Agent: `metaso-py/<version>`

## Path Management

Uses `platformdirs` for cross-platform config paths:

```python
from platformdirs import user_config_dir, user_data_dir

def get_home_dir() -> Path:
    if home := os.environ.get("METASO_HOME"):
        return Path(home)
    return Path(user_config_dir("metaso"))
    # macOS: ~/Library/Application Support/metaso
    # Linux: ~/.config/metaso
    # Windows: C:\Users\<user>\AppData\Local\metaso
```

Profile-based directory structure:
```
<config_dir>/
├── config.json              # Global config (default_profile, etc.)
└── profiles/
    ├── default/
    │   └── cookies.json     # CookieAuth storage
    └── work/
        └── cookies.json
```

## CLI

All commands support `--json` for structured output and `--profile` for multi-account.

### Phase 1 Commands

```bash
metaso config set api-key <key>           # Store API key
metaso config set backend <official|unofficial|auto>
metaso status                             # Auth status, active backend, profile

metaso search "query"                     # Default (concise) mode
metaso search "query" --mode detail       # Modes: concise, detail, research
metaso search "query" --mode scholar      # Academic search
metaso search "query" --stream            # SSE streaming output
metaso search "query" --json              # JSON output
```

### Phase 2 Commands

```bash
metaso login                              # agent-browser login
metaso logout                             # Clear stored credentials
metaso config set cookie <uid-sid>        # Manual cookie config

metaso topic create "name" [--json]
metaso topic list [--json]
metaso topic delete <id>

metaso file upload <path> --topic <id> [--json]
metaso file list --topic <id> [--json]
metaso file delete <id>

metaso book add <url> --topic <id> [--json]
metaso book list --topic <id> [--json]

metaso user info [--json]
```

### Phase 3 Commands

```bash
metaso skill install                      # Install Claude Code SKILL.md
```

### JSON Output Format

```json
// metaso search "AI" --json
{
  "query": "AI",
  "results": [
    {"id": "...", "title": "...", "url": "...", "snippet": "...", "source": "webpage"}
  ],
  "summary": "AI is...",
  "session_id": "abc123"
}

// metaso topic list --json
{"topics": [{"id": "...", "name": "...", "created_at": "..."}]}

// metaso status --json
{"backend": "official", "profile": "default", "authenticated": true}
```

## Build & Dependencies

### pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "metaso-py"
requires-python = ">=3.10"
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
```

## Testing Strategy

- **Unit** (`tests/unit/`): Types, encoding, path resolution. No network.
- **Integration** (`tests/integration/`): Mock HTTP via respx. Test client → backend → response parsing.
- **E2E** (`tests/e2e/`): Real API calls. Marked `@pytest.mark.e2e`, excluded by default.

Quality gates:
```bash
ruff format src/ tests/
ruff check src/ tests/
mypy src/metaso --ignore-missing-imports
pytest
```

## Claude Code Skill (Phase 3)

SKILL.md follows the notebooklm skill format:

- Installation & auth guide
- Quick reference table (all commands)
- Autonomy rules (auto-run vs ask-before-run)
- Error handling decision tree
- JSON output schemas
- Installed via `metaso skill install` to `~/.claude/skills/metaso/SKILL.md`

## Reference Projects

| Project | Role | Key Takeaway |
|---------|------|-------------|
| notebooklm-py | Architecture reference | Layered design, CLI patterns, skill format, paths.py |
| metaso-sdk | Official API reference | Endpoint shapes, types, search/topic/file APIs |
| metaso-free-api | Unofficial API reference | uid-sid auth, SSE streaming, search modes, meta-token extraction |
| metaso-sse | Search API reference | Search endpoint format, MCP patterns |

## Codex Review Feedback (Incorporated)

| Feedback | Resolution |
|----------|-----------|
| Too much structure for v1 | Phased delivery: Phase 1 = official + search only |
| Need capability model | `BackendBase.supports()` + default `BackendError` raises |
| Missing transport policy | Explicit timeout/retry/backoff in `_core.py` |
| Use platformdirs | Adopted for cross-platform paths |
| Missing test strategy for unofficial | respx fixtures + separate e2e marks |
| skill is distribution noise | Moved to Phase 3 |
| Unified types may be false abstraction | Validated: metaso-sdk and metaso-free-api search formats are highly consistent |
| agent-browser feasibility risk | Accepted: user requirement, notebooklm-py validates similar approach |
