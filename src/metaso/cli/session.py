"""Session management: config, status, login, logout."""

from __future__ import annotations

import json
import os
import subprocess
import time

import click

from metaso.paths import get_config_path, get_cookie_path, get_profile_dir


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
        cookie_path = get_cookie_path(profile)
        if cookie_path.exists():
            click.echo("Auth: cookie (uid-sid)")
            click.echo("Backend: unofficial")
        else:
            click.echo("API Key: not configured")
    config_path = get_config_path()
    click.echo(f"Config: {config_path}")


@click.command("login")
@click.pass_context
def login_cmd(ctx):
    """Login to Metaso via browser (extracts cookies automatically)."""
    profile = ctx.obj.get("profile") or "default"

    click.echo("Opening Metaso in browser...")
    click.echo("Please complete login (phone number or WeChat scan).")
    click.echo()

    try:
        subprocess.run(
            ["agent-browser", "open", "https://metaso.cn"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        click.echo("Error: agent-browser not found. Install it first.", err=True)
        click.echo(
            "Alternatively, set cookie manually: metaso config set cookie <uid-sid>", err=True
        )
        raise SystemExit(1)

    subprocess.run(
        ["agent-browser", "wait", "--load", "networkidle"],
        capture_output=True,
        text=True,
    )

    click.echo("Waiting for login... (press Ctrl+C to cancel)")

    max_attempts = 60  # 5 minutes at 5s intervals
    for attempt in range(max_attempts):
        result = subprocess.run(
            ["agent-browser", "eval", "document.cookie"],
            capture_output=True,
            text=True,
        )
        cookie_str = result.stdout.strip()

        cookies = {}
        for part in cookie_str.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                cookies[k.strip()] = v.strip()

        if "uid" in cookies and "sid" in cookies:
            profile_dir = get_profile_dir(profile, create=True)
            cookie_file = profile_dir / "cookies.json"
            cookie_file.write_text(
                json.dumps({"uid": cookies["uid"], "sid": cookies["sid"]}, indent=2),
                encoding="utf-8",
            )

            subprocess.run(["agent-browser", "close"], capture_output=True, text=True)

            click.echo(f"Login successful! Cookies saved to {cookie_file}")
            click.echo(f"  uid: {cookies['uid'][:8]}...")
            click.echo(f"  sid: {cookies['sid'][:8]}...")
            return

        time.sleep(5)

    subprocess.run(["agent-browser", "close"], capture_output=True, text=True)
    click.echo("Login timed out. Please try again.", err=True)
    raise SystemExit(1)


@click.command("logout")
@click.pass_context
def logout_cmd(ctx):
    """Clear stored credentials."""
    profile = ctx.obj.get("profile") or "default"
    cookie_path = get_cookie_path(profile)
    if cookie_path.exists():
        cookie_path.unlink()
        click.echo(f"Credentials cleared for profile '{profile}'.")
    else:
        click.echo(f"No credentials found for profile '{profile}'.")


@click.group("config")
def config_group():
    """Manage configuration."""


@config_group.command("set")
@click.argument("key", type=click.Choice(["api-key", "backend", "cookie"]))
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
    elif key == "cookie":
        # Parse uid-sid format
        parts = value.split("-", 1)
        if len(parts) != 2:
            raise click.BadParameter("Cookie must be in uid-sid format")
        profile_dir = get_profile_dir(create=True)
        cookie_file = profile_dir / "cookies.json"
        cookie_file.write_text(
            json.dumps({"uid": parts[0], "sid": parts[1]}, indent=2),
            encoding="utf-8",
        )
        click.echo(f"Cookie saved to {cookie_file}")
        return

    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
