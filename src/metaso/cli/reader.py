"""Read URL command."""

from __future__ import annotations

from dataclasses import asdict

import click

from metaso.cli.helpers import async_command, get_client, output_json


@click.command("read")
@click.argument("url")
@click.option("--format", "fmt", default="markdown", type=click.Choice(["json", "markdown"]))
@click.option("--json", "json_output", is_flag=True, help="JSON output.")
@click.pass_context
@async_command
async def read_cmd(ctx, url, fmt, json_output):
    """Read content from a URL."""
    client = get_client(ctx)
    async with client:
        result = await client.reader.read(url, format=fmt)
        if json_output:
            output_json(asdict(result))
        else:
            click.echo(result.content)
