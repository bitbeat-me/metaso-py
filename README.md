# metaso-py

**Metaso AI Search Python Client.** Search, read URLs, RAG chat, and manage knowledge bases via Python, CLI, and AI agents like Claude Code.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://pypi.org/project/metaso-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

| Category | Capabilities |
|----------|-------------|
| **Search** | Web, document, paper, image, video, podcast scopes |
| **Search Modes** | Concise (~3s), Detail (~5s), Deep Research (30-120s) |
| **Read URL** | Extract content from any URL as markdown or JSON |
| **Chat** | RAG intelligent Q&A based on search results |
| **Topics** | Create, list, delete knowledge base topics |
| **Files** | Upload, list, delete files in topics |
| **Bookshelf** | Add and manage books/PDFs |
| **Streaming** | Progressive SSE output for all search modes |
| **Dual Backend** | Official API (API key) + reverse-engineered API (browser cookie) |

## Three Ways to Use

| Method | Best For |
|--------|----------|
| **Python API** | Application integration, async workflows |
| **CLI** | Shell scripts, agent automation |
| **Claude Code Skill** | AI agent integration via `/metaso` |

## Quick Start

### Install

```bash
pip install metaso-py
```

### Configure

```bash
# Option 1: API Key (get from https://metaso.cn/search-api/api-keys)
cp .env.example .env
# Edit .env with your API key

# Option 2: Environment variable
export METASO_API_KEY=mk-your-api-key

# Option 3: CLI config
metaso config set api-key mk-your-api-key

# Option 4: Browser login (cookie-based)
metaso login
```

### Search

```bash
# Basic search
metaso search "AI agent trends"

# Deep research (full AI analysis report)
metaso search "AI agent trends" --mode research

# Stream results progressively
metaso search "AI agent trends" --mode research --stream

# Academic papers
metaso search "transformer architecture" --scope paper

# JSON output (for scripting/agents)
metaso search "Claude Code" --json
```

### Read & Chat

```bash
# Read URL content as markdown
metaso read "https://example.com"

# RAG Q&A
metaso chat "what is MCP protocol"
```

### Knowledge Base

```bash
# Topics
metaso topic create "My Research"
metaso topic list --json
metaso topic delete <id>

# Files
metaso file upload ./paper.pdf --topic <id>
metaso file list --topic <id> --json

# Bookshelf
metaso book add "https://example.com/paper.pdf" --topic <id>
```

## Python API

```python
import asyncio
from metaso import MetasoClient

async def main():
    async with MetasoClient.from_api_key("mk-your-key") as client:
        # Search
        result = await client.search.query("AI trends", mode="research")
        print(result.summary)

        # Read URL
        page = await client.reader.read("https://example.com")
        print(page.content)

        # Chat
        answer = await client.chat.ask("what is RAG?")
        print(answer.answer)

        # Topics & files
        topic = await client.topics.create("Research")
        file = await client.files.upload(topic.id, "paper.pdf")

asyncio.run(main())
```

### Auto-detect credentials

```python
# Reads METASO_API_KEY from environment or .env file
# Falls back to stored browser cookies
async with MetasoClient.auto() as client:
    result = await client.search.query("test")
```

## Claude Code Skill

Install the skill for AI agent integration:

```bash
metaso skill install
```

Then use `/metaso` in Claude Code, or the agent will auto-activate on search intents.

### Deep Research (Agent Pattern)

For long-running research in agent workflows, dispatch to a background subagent:

```python
Agent(
    prompt='Run this command and return the full output:\n'
           'metaso search "AI agent trends" --mode research --json',
    subagent_type="general-purpose",
    run_in_background=True,
)
```

## Architecture

```
CLI (click)
    |
MetasoClient + namespaced APIs (search, reader, chat, topics, files, bookshelf, user)
    |
ClientCore (httpx lifecycle, transport policy)
    |
Backend (abstract)
    |- OfficialBackend (API key -> /api/open/*)
    |- UnofficialBackend (uid-sid cookies -> reverse-engineered API)
```

Follows [notebooklm-py](https://github.com/teng-lin/notebooklm-py) layered architecture.

## Development

```bash
# Setup
git clone https://github.com/your-org/metaso-py.git
cd metaso-py
uv venv .venv && uv pip install -e ".[dev]"
cp .env.example .env  # Add your API key

# Test
pytest

# Quality
ruff format src/ tests/
ruff check src/ tests/
mypy src/metaso --ignore-missing-imports
```

## Acknowledgments

- [notebooklm-py](https://github.com/teng-lin/notebooklm-py) - Architecture reference. metaso-py follows its layered design (CLI / Client / Core / Backend), skill format, and login flow.
- [metaso-sdk](https://github.com/meta-sota/metaso-sdk) - Official Metaso Python SDK. Provided API endpoint shapes and data models.
- [metaso-free-api](https://github.com/LLM-Red-Team/metaso-free-api) - Reverse-engineered Metaso API. Provided uid-sid auth pattern and SSE streaming reference.
- [Metaso AI Search](https://metaso.cn) - The search service this client wraps.

## License

MIT
