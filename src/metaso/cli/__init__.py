"""Metaso CLI - command line interface."""

import click

from metaso.cli.chat import chat_cmd
from metaso.cli.reader import read_cmd
from metaso.cli.search import search_cmd
from metaso.cli.session import config_group, status_cmd


@click.group()
@click.version_option(package_name="metaso-py")
@click.option("--profile", default=None, help="Profile name for multi-account support.")
@click.pass_context
def cli(ctx, profile):
    """Metaso AI Search - Python client."""
    ctx.ensure_object(dict)
    ctx.obj["profile"] = profile


cli.add_command(search_cmd, "search")
cli.add_command(read_cmd, "read")
cli.add_command(chat_cmd, "chat")
cli.add_command(status_cmd, "status")
cli.add_command(config_group, "config")
