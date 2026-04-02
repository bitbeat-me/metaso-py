---
name: metaso
description: Metaso AI search - search web/academic sources, read URLs, RAG chat, manage topics and files. Activates on explicit /metaso or intent like "search for X on Metaso"
---
<!-- metaso-py v0.1.0 -->

# Metaso AI Search

Python client for Metaso AI search with dual backend support.

## Prerequisites

```bash
pip install metaso-py
metaso status              # Check auth
metaso config set api-key <key>  # Set API key (from https://metaso.cn/search-api/api-keys)
# OR
metaso login               # Browser login (cookie-based, for unofficial backend)
```

## API Coverage

### Official Backend (API Key)

Verified against real API. All endpoints tested.

| Task | Command | Verified |
|------|---------|:--------:|
| Search | `metaso search "query"` | Yes |
| Search (scope) | `metaso search "query" --scope paper` | Yes |
| Search (modes) | `metaso search "query" --mode research` | Yes |
| Search (stream) | `metaso search "query" --mode research --stream` | Yes |
| Read URL | `metaso read "https://..."` | Yes |
| Chat (RAG) | `metaso chat "question"` | Yes |
| Create topic | `metaso topic create "name" --json` | Yes |
| Delete topic | `metaso topic delete <id>` | Yes |
| Upload file | `metaso file upload ./file.pdf --dir-root-id <id> --json` | Yes |
| File progress | `metaso file progress <file_id>` | Yes |
| Delete file | `metaso file delete <id>` | Yes |
| Add book | `metaso book add <url> --json` | Yes |

### Unofficial Backend (Cookie auth via `metaso login`)

Uses reverse-engineered web API. May break if Metaso changes their frontend.

| Task | Command | Note |
|------|---------|------|
| Search | `metaso search "query"` | Uses session + SSE streaming |
| Search (stream) | `metaso search "query" --stream` | Progressive output |

### Not Available

These have no known API endpoint (official or unofficial):

- List topics
- List files
- List books
- User info

## Quick Reference

| Task | Command | Backend |
|------|---------|---------|
| Check status | `metaso status` | - |
| Auth check | `metaso auth-check` | - |
| Set API key | `metaso config set api-key <key>` | - |
| Set cookie | `metaso config set cookie <uid-sid>` | - |
| Browser login | `metaso login` | - |
| Logout | `metaso logout` | - |
| Search | `metaso search "query" [--scope X] [--mode X] [--stream] [--json]` | Both |
| Read URL | `metaso read "https://..." [--format json\|markdown] [--json]` | Official |
| Chat | `metaso chat "question" [--json]` | Official |
| Create topic | `metaso topic create "name" [--json]` | Official |
| Delete topic | `metaso topic delete <id>` | Official |
| Upload file | `metaso file upload <path> --dir-root-id <id> [--json]` | Official |
| File progress | `metaso file progress <file_id>` | Official |
| Delete file | `metaso file delete <id>` | Official |
| Add book | `metaso book add <url> [--json]` | Official |
| Install skill | `metaso skill install` | - |

**Search scopes:** webpage, document, paper, image, video, podcast
**Search modes:** concise (~3s), detail (~5s), research (30-120s)

## Autonomy Rules

**Run automatically (no confirmation):**
- `metaso status` / `metaso auth-check`
- `metaso search` - execute searches
- `metaso read` - read URL content
- `metaso chat` - RAG Q&A
- `metaso file progress` - check processing status

**Ask before running:**
- `metaso login` - opens browser
- `metaso logout` - clears credentials
- `metaso topic create` / `metaso topic delete` - modifies data
- `metaso file upload` / `metaso file delete` - modifies data
- `metaso book add` - modifies data
- `metaso config set` - modifies config

## Deep Research (Background Pattern)

Deep research (`--mode research`) can take 30-120 seconds.

**Streaming (recommended):**
```bash
metaso search "AI agent trends" --mode research --stream
```

**Agent background pattern (non-blocking):**
```python
Agent(
    prompt='Run this command and return the full output:\n'
           'metaso search "AI agent trends" --mode research --json',
    subagent_type="general-purpose",
    run_in_background=True,
)
```

## Typical Workflow

```bash
# 1. Create topic and note the dirRootId
metaso topic create "My Research" --json
# → {"id": "123", "name": "My Research", "dir_root_id": "456"}

# 2. Upload files using dirRootId (not topic id)
metaso file upload paper.pdf --dir-root-id 456 --json
# → {"id": "789", "file_name": "paper.pdf", ...}

# 3. Check processing progress
metaso file progress 789
# → Progress: 100%

# 4. Search with topic context (via session)
metaso search "summarize the paper" --mode research
```

## JSON Output

```json
// metaso search "AI" --json
{"query": "AI", "results": [...], "summary": "...", "session_id": "..."}

// metaso read "https://..." --json
{"url": "...", "content": "...", "format": "markdown"}

// metaso chat "question" --json
{"message": "...", "answer": "...", "model": "fast"}

// metaso topic create "X" --json
{"id": "...", "name": "X", "dir_root_id": "...", "created_at": null}
```

## Error Handling

| Error | Action |
|-------|--------|
| "No credentials found" | `metaso config set api-key <key>` or `metaso login` |
| "Invalid API key" | Check key at https://metaso.cn/search-api/api-keys |
| "meta-token not found" | Session expired, run `metaso login` |
| "Rate limit exceeded" | Wait and retry |
| "does not support" | Operation not available on current backend |

## Multi-Account

```bash
metaso --profile work config set api-key <key>
metaso --profile work search "query"
```
