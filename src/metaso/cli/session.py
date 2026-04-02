"""Session management: config, status."""

from __future__ import annotations

import json
import os

import click

from metaso.paths import get_config_path


@click.command("status")
@click.pass_context
def status_cmd(ctx):
    """Show authentication status."""
    api_key = os.environ.get("METASO_API_KEY")
    profile = ctx.obj.get("profile", "default") or "default"
    click.echo(f"Profile: {profile}")
    if api_key:
        masked = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
        click.echo(f"API Key: {masked}")
        click.echo("Backend: official")
    else:
        click.echo("API Key: not configured")
    config_path = get_config_path()
    click.echo(f"Config: {config_path}")


@click.group("config")
def config_group():
    """Manage configuration."""


@config_group.command("set")
@click.argument("key", type=click.Choice(["api-key", "backend"]))
@click.argument("value")
def config_set(key, value):
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
            raise click.BadParameter("Must be: official, unofficial, auto")
        config["backend"] = value
        click.echo(f"Backend set to: {value}")
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
