from __future__ import annotations

from dataclasses import asdict

import click

from metaso.cli.helpers import async_command, get_client, output_json


@click.command("user")
@click.option("--json", "json_output", is_flag=True)
@click.pass_context
@async_command
async def user_cmd(ctx, json_output):
    """Show user information."""
    client = get_client(ctx)
    async with client:
        info = await client.user.info()
        if json_output:
            output_json(asdict(info))
        else:
            click.echo(f"UID: {info.uid}")
            if info.nickname:
                click.echo(f"Nickname: {info.nickname}")
            click.echo(f"VIP Level: {info.vip_level}")
