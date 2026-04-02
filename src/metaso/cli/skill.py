"""Skill installation command."""

from __future__ import annotations

from pathlib import Path

import click

SKILL_CONTENT = """---
name: metaso
description: Metaso AI search - full programmatic access. Search web/academic sources, read URLs, RAG chat, manage knowledge base topics, upload files. Activates on explicit /metaso or intent like "search for X on Metaso"
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
| Set cookie | `metaso config set cookie <uid-sid>` |
| Browser login | `metaso login` |
| Logout | `metaso logout` |
| Search (webpage) | `metaso search "query"` |
| Search (paper) | `metaso search "query" --scope paper` |
| Search (all scopes) | `metaso search "query" --scope <webpage\\|document\\|paper\\|image\\|video\\|podcast>` |
| Search (with summary) | `metaso search "query" --include-summary` |
| Search (JSON) | `metaso search "query" --json` |
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
"""


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
