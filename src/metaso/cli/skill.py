"""Skill installation command."""

from __future__ import annotations

from pathlib import Path

import click

# Repo root SKILL.md (used when running from source checkout)
_REPO_SKILL = Path(__file__).resolve().parents[3] / "SKILL.md"


def _get_skill_content() -> str:
    """Read skill content from repo root or package data."""
    # Prefer repo root (source checkout / development)
    if _REPO_SKILL.exists():
        return _REPO_SKILL.read_text(encoding="utf-8")

    # Fallback: package data (pip install)
    try:
        from importlib import resources

        return (resources.files("metaso") / "data" / "SKILL.md").read_text(encoding="utf-8")
    except (FileNotFoundError, TypeError, ModuleNotFoundError):
        pass

    raise FileNotFoundError(
        "SKILL.md not found. This may indicate a corrupted installation.\n"
        "Try reinstalling: pip install --force-reinstall metaso-py"
    )


@click.group("skill")
def skill_group():
    """Manage Claude Code skill."""


@skill_group.command("install")
def skill_install():
    """Install the Metaso Claude Code skill."""
    content = _get_skill_content()
    skill_dir = Path.home() / ".claude" / "skills" / "metaso"
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(content, encoding="utf-8")
    click.echo(f"Skill installed to {skill_path}")
    click.echo("Restart Claude Code to activate the /metaso skill.")


@skill_group.command("show")
def skill_show():
    """Show the current skill content."""
    content = _get_skill_content()
    click.echo(content)
