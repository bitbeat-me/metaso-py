---
name: metaso
description: Metaso AI search - full programmatic access. Search web/academic sources, read URLs, RAG chat, manage knowledge base topics, upload files. Activates on explicit /metaso or intent like "search for X on Metaso"
---
<!-- metaso-py v0.1.0 -->

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
| Set cookie | `metaso config set cookie <uid-sid>` |
| Browser login | `metaso login` |
| Logout | `metaso logout` |
| Auth check | `metaso auth-check` |
| Search (webpage) | `metaso search "query"` |
| Search (paper) | `metaso search "query" --scope paper` |
| Search (all scopes) | `metaso search "query" --scope <webpage\|document\|paper\|image\|video\|podcast>` |
| Search (with summary) | `metaso search "query" --include-summary` |
| Search (JSON) | `metaso search "query" --json` |
| Deep research | `metaso search "query" --mode research` |
| Deep research (stream) | `metaso search "query" --mode research --stream` |
| Read URL | `metaso read "https://..." --json` |
| Read URL (markdown) | `metaso read "https://..." --format markdown` |
| Chat (RAG Q&A) | `metaso chat "question" --json` |
| Create topic | `metaso topic create "name" --json` |
| List topics | `metaso topic list --json` |
| Delete topic | `metaso topic delete <id>` |
| Upload file | `metaso file upload ./file.pdf --topic <id> --json` |
| List files | `metaso file list --topic <id> --json` |
| Delete file | `metaso file delete <id>` |
| Add book | `metaso book add <url> --topic <id> --json` |
| List books | `metaso book list --topic <id> --json` |
| User info | `metaso user --json` |

## Autonomy Rules

**Run automatically (no confirmation):**
- `metaso status` - check state
- `metaso auth-check` - verify credentials
- `metaso search` - execute searches
- `metaso read` - read URL content
- `metaso chat` - RAG Q&A
- `metaso topic list` - list topics
- `metaso file list` - list files
- `metaso book list` - list books
- `metaso user` - user info

**Ask before running:**
- `metaso login` - opens browser
- `metaso logout` - clears credentials
- `metaso topic create` - creates resource
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

// metaso read "https://..." --json
{"url": "...", "content": "...", "format": "markdown"}

// metaso chat "question" --json
{"message": "...", "answer": "...", "model": "fast"}

// metaso topic list --json
{"topics": [{"id": "...", "name": "...", "dir_root_id": "..."}]}

// metaso status (text only)
Profile: default
API Key: sk-xxx...xxxx
Backend: official
```

## Deep Research (Background Pattern)

Deep research (`--mode research`) can take 30-120 seconds. For non-blocking usage,
use `--stream` which returns results progressively as they are generated.

**Interactive (blocking):**
```bash
metaso search "AI agent trends" --mode research
```

**Streaming (progressive, recommended):**
```bash
metaso search "AI agent trends" --mode research --stream
```

**Agent background pattern (non-blocking):**
When running deep research from an agent context, dispatch to a background subagent
so the main conversation continues while research runs:

```python
Agent(
    prompt='Run this command and return the full output:\n'
           'metaso search "AI agent trends" --mode research --json',
    subagent_type="general-purpose",
    run_in_background=True,
)
```

The subagent runs the research, and the agent is notified when it completes.
This is the recommended pattern for deep research in agent workflows.

**Search modes:**
| Mode | Speed | Output |
|------|-------|--------|
| `concise` | Fast (~3s) | References + short summary |
| `detail` | Medium (~5s) | References + detailed summary |
| `research` | Slow (30-120s) | Full AI analysis report + many references + follow-up questions |

**Note:** `metaso chat` uses the search API internally (mode=fast). For deeper
answers, use `metaso search "question" --mode research` instead.

## Error Handling

| Error | Action |
|-------|--------|
| "No credentials found" | Run `metaso config set api-key <key>` or `metaso login` |
| "Invalid API key" | Check METASO_API_KEY or re-set via config |
| "meta-token not found" | Session expired, run `metaso login` |
| "Rate limit exceeded" | Wait and retry |
| "does not support" | Operation not available on current backend |

## Multi-Account

Use `--profile` for multiple accounts:
```bash
metaso --profile work config set api-key <key>
metaso --profile work search "query"
```
