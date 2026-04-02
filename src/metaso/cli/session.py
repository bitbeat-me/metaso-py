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
            data = json.loads(cookie_path.read_text(encoding="utf-8"))
            click.echo(f"Auth: cookie (uid: {data.get('uid', '?')[:8]}...)")
            click.echo("Backend: unofficial")
        else:
            click.echo("API Key: not configured")
    config_path = get_config_path()
    click.echo(f"Config: {config_path}")


def _run_browser(*args: str, timeout: int = 60) -> str | None:
    """Run an agent-browser command with --session-name metaso. Returns stdout or None on failure."""
    try:
        result = subprocess.run(
            ["agent-browser", "--session-name", "metaso", *args],
            capture_output=True, text=True, timeout=timeout,
        )
        # agent-browser uses ANSI codes and non-zero exit for non-fatal issues
        output = (result.stdout or "") + (result.stderr or "")
        return output.strip() if output.strip() else ""
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return ""


def _extract_cookies_from_browser() -> dict[str, str] | None:
    """Try to extract uid/sid cookies from the current agent-browser page."""
    output = _run_browser("eval", "document.cookie")
    if not output:
        return None
    cookie_str = output
    cookies = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()
    if "uid" in cookies and "sid" in cookies:
        return cookies
    return None


def _save_cookies(cookies: dict[str, str], profile: str) -> None:
    """Save uid/sid cookies to profile directory."""
    profile_dir = get_profile_dir(profile, create=True)
    cookie_file = profile_dir / "cookies.json"
    cookie_file.write_text(
        json.dumps({"uid": cookies["uid"], "sid": cookies["sid"]}, indent=2),
        encoding="utf-8",
    )


def _try_silent_refresh(profile: str) -> bool:
    """Try to refresh cookies using persisted agent-browser session.

    Returns True if cookies were successfully refreshed without user interaction.
    """
    if _run_browser("open", "https://metaso.cn", timeout=30) is None:
        return False
    _run_browser("wait", "--load", "networkidle", timeout=30)
    cookies = _extract_cookies_from_browser()
    if cookies:
        _save_cookies(cookies, profile)
        _run_browser("close")
        return True
    _run_browser("close")
    return False


@click.command("login")
@click.option("--force", is_flag=True, help="Force interactive login even if session exists.")
@click.pass_context
def login_cmd(ctx, force):
    """Login to Metaso via browser.

    First login requires browser interaction. Subsequent logins attempt
    silent session refresh — you only need to interact again if the
    session has fully expired.
    """
    profile = ctx.obj.get("profile") or "default"

    # Try silent refresh first (unless --force)
    if not force:
        cookie_path = get_cookie_path(profile)
        if cookie_path.exists():
            click.echo("Attempting silent session refresh...")
            if _try_silent_refresh(profile):
                click.echo("Session refreshed successfully! No login needed.")
                return
            click.echo("Session expired. Opening browser for login...")

    click.echo("Opening Metaso in browser...")
    click.echo("Please complete login (phone number or WeChat scan).")
    click.echo()

    if _run_browser("open", "https://metaso.cn", timeout=30) is None:
        click.echo("Error: agent-browser not found or failed to open.", err=True)
        click.echo("Alternative: metaso config set cookie <uid-sid>", err=True)
        raise SystemExit(1)
    _run_browser("wait", "--load", "networkidle", timeout=30)

    click.echo("Waiting for login... (press Ctrl+C to cancel)")

    max_attempts = 60  # 5 minutes at 5s intervals
    for attempt in range(max_attempts):
        cookies = _extract_cookies_from_browser()
        if cookies:
            _save_cookies(cookies, profile)
            _run_browser("close")
            click.echo("\nLogin successful!")
            click.echo(f"  uid: {cookies['uid'][:8]}...")
            click.echo(f"  sid: {cookies['sid'][:8]}...")
            click.echo("  Session persisted for future silent refresh.")
            return

        time.sleep(5)

    _run_browser("close")
    click.echo("Login timed out. Please try again.", err=True)
    raise SystemExit(1)


@click.command("logout")
@click.pass_context
def logout_cmd(ctx):
    """Clear stored credentials and browser session."""
    profile = ctx.obj.get("profile") or "default"
    cookie_path = get_cookie_path(profile)
    cleared = False
    if cookie_path.exists():
        cookie_path.unlink()
        cleared = True
    _run_browser("close")
    if cleared:
        click.echo(f"Credentials and browser session cleared for profile '{profile}'.")
    else:
        click.echo(f"No credentials found for profile '{profile}'.")


@click.command("auth-check")
@click.pass_context
def auth_check_cmd(ctx):
    """Verify authentication is valid."""
    import asyncio

    profile = ctx.obj.get("profile") or "default"
    api_key = os.environ.get("METASO_API_KEY")

    if api_key:
        click.echo("API Key: configured")
        click.echo("Status: valid (API keys don't expire)")
        return

    cookie_path = get_cookie_path(profile)
    if not cookie_path.exists():
        click.echo("Status: not authenticated")
        click.echo("Run 'metaso login' or 'metaso config set api-key <key>'")
        return

    click.echo("Cookie: found")
    click.echo("Validating...")

    from metaso.client import MetasoClient

    try:
        client = MetasoClient.from_storage(profile=profile)
    except Exception as e:
        click.echo(f"Status: invalid ({e})")
        return

    async def _check():
        async with client:
            return await client.validate_auth()

    valid = asyncio.run(_check())
    if valid:
        click.echo("Status: valid")
    else:
        click.echo("Status: expired")
        click.echo("Run 'metaso login' to refresh.")


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
